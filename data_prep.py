"""
Carga, limpeza e engenharia de features do dataset de incidentes.

Este módulo lê o LW-DATASET.xlsx (schema documentado no "Dicionário de
Dados - v2") e produz dois artefatos usados pelo resto do pipeline:

1. `build_daily_volume_table`  -> série diária de volume (para os modelos
   de previsão D+1 / D+7).
2. `build_ticket_level_table`  -> uma linha por chamado, com as features
   usadas pelo classificador de risco de quebra de OLA.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


# --------------------------------------------------------------------------
# Carga bruta
# --------------------------------------------------------------------------
def load_raw_dataset(path=None) -> pd.DataFrame:
    """Lê o dataset bruto de incidentes e normaliza tipos básicos."""
    path = path or config.RAW_DATASET_PATH
    df = pd.read_excel(path, sheet_name=config.RAW_DATASET_SHEET)

    # Datas
    for col in ["Aberto", "Resolvido", "Encerrado"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Normaliza campos texto usados como chave de agrupamento
    text_cols = [
        "Prioridade", "Produto", "Categoria", "Subcategoria",
        "Grupo designado", "Item de configuração", "Status",
        "Aberto por", "Entrou para KPI?", "KPI Violado?",
    ]
    for col in text_cols:
        df[col] = df[col].astype("string").str.strip()

    return df


# --------------------------------------------------------------------------
# Features de calendário (reaproveitadas nas duas tabelas)
# --------------------------------------------------------------------------
def _add_calendar_features(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    dt = df[date_col]
    df["dia_semana"] = dt.dt.dayofweek  # 0=segunda ... 6=domingo
    df["is_weekend"] = df["dia_semana"].isin([5, 6]).astype(int)
    df["is_month_start"] = dt.dt.is_month_start.astype(int)
    df["is_month_end"] = dt.dt.is_month_end.astype(int)
    df["hora_abertura"] = dt.dt.hour
    df["is_noturno"] = df["hora_abertura"].apply(lambda h: 1 if (h >= 22 or h < 6) else 0)
    df["is_troca_turno"] = df["hora_abertura"].isin([6, 7, 13, 14, 18, 19]).astype(int)
    return df


# --------------------------------------------------------------------------
# 1) Série diária de volume (para previsão D+1 / D+7)
# --------------------------------------------------------------------------
def build_daily_volume_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega o dataset em uma linha por dia, com o volume total e por
    prioridade (P2/P3), pronto para engenharia de lags/médias móveis.
    """
    work = df.copy()
    work["data"] = work["Aberto"].dt.floor("D")

    is_p2p3 = work["Prioridade"].isin(config.FORECAST_PRIORITIES)
    is_kpi_elig = work["Entrou para KPI?"] == "SIM"
    is_kpi_viol = work["KPI Violado?"] == "SIM"

    daily = (
        work.assign(is_p2p3=is_p2p3, is_kpi_elig=is_kpi_elig, is_kpi_viol=is_kpi_viol)
        .groupby("data")
        .agg(
            volume_total=("Número", "count"),
            volume_p2p3=("is_p2p3", "sum"),
            volume_kpi_elegivel=("is_kpi_elig", "sum"),
            volume_kpi_violado=("is_kpi_viol", "sum"),
        )
        .reset_index()
    )

    # Preenche dias sem nenhum chamado (não deveria existir no regime atual,
    # mas protege o pipeline caso haja lacunas na extração).
    full_range = pd.date_range(daily["data"].min(), daily["data"].max(), freq="D")
    daily = (
        daily.set_index("data")
        .reindex(full_range)
        .fillna(0)
        .rename_axis("data")
        .reset_index()
    )
    for col in ["volume_total", "volume_p2p3", "volume_kpi_elegivel", "volume_kpi_violado"]:
        daily[col] = daily[col].astype(int)

    daily = _add_calendar_features(daily, "data")

    # Lags e médias móveis (features preditivas do dia t)
    for target_col in ["volume_total", "volume_p2p3"]:
        for lag in [1, 2, 3, 7, 14]:
            daily[f"{target_col}_lag{lag}"] = daily[target_col].shift(lag)
        daily[f"{target_col}_roll_mean_7"] = daily[target_col].shift(1).rolling(7).mean()
        daily[f"{target_col}_roll_std_7"] = daily[target_col].shift(1).rolling(7).std()

    return daily


def restrict_to_current_regime(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Recorta a série diária para o regime operacional atual (pós-automação
    do monitoramento), mantendo alguns dias anteriores só como warm-up
    para lags/médias móveis do primeiro dia do novo regime.
    """
    break_date = pd.Timestamp(config.REGIME_BREAK_DATE)
    warmup_start = break_date - pd.Timedelta(days=config.WARMUP_DAYS)
    windowed = daily[daily["data"] >= warmup_start].copy()
    return windowed[windowed["data"] >= break_date].reset_index(drop=True), windowed


# --------------------------------------------------------------------------
# 2) Tabela em nível de chamado (para o classificador de risco de OLA)
# --------------------------------------------------------------------------
def _frequency_encode(series: pd.Series) -> pd.Series:
    freq = series.value_counts(dropna=False)
    return series.map(freq).astype(float)


def build_ticket_level_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna uma linha por chamado elegível ao KPI (Entrou para KPI = SIM),
    com as features usadas para prever `kpi_violado` (1 = quebrou o OLA).
    """
    work = df[df["Entrou para KPI?"] == "SIM"].copy()
    work = _add_calendar_features(work, "Aberto")

    work["kpi_violado"] = (work["KPI Violado?"] == "SIM").astype(int)

    # Frequência global de cada dimensão categórica: equipes, ativos e
    # produtos recorrentes tendem a concentrar risco (achado da Sprint 3 -
    # XAI). Usar frequência (em vez de one-hot) mantém uma única feature por
    # dimensão de negócio, o que deixa a importância do modelo diretamente
    # interpretável (ex.: "Grupo designado" pesa X% na previsão).
    work["grupo_designado_freq"] = _frequency_encode(work["Grupo designado"])
    work["item_configuracao_freq"] = _frequency_encode(work["Item de configuração"].fillna("DESCONHECIDO"))
    work["produto_freq"] = _frequency_encode(work["Produto"].fillna("DESCONHECIDO"))
    work["categoria_freq"] = _frequency_encode(work["Categoria"].fillna("DESCONHECIDA"))

    # Prioridade textual ("2 - Alta") -> ordinal numérico (2)
    work["prioridade_ordinal"] = (
        work["Prioridade"].str.extract(r"^(\d)")[0].astype(float)
    )

    feature_cols = [
        "prioridade_ordinal", "grupo_designado_freq", "item_configuracao_freq",
        "produto_freq", "categoria_freq", "dia_semana", "is_weekend",
        "is_noturno", "is_troca_turno", "hora_abertura",
    ]
    id_cols = ["Número", "Aberto", "Grupo designado", "Produto", "Item de configuração"]

    result = work[id_cols + feature_cols + ["kpi_violado"]].copy()
    result = result.dropna(subset=feature_cols)
    return result
