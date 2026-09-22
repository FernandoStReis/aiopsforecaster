"""
Diagnóstico operacional e camada prescritiva.

Agrega os chamados e as violações de OLA por equipe, produto e ativo de
configuração, e gera recomendações práticas de onde agir — os mesmos
elementos usados no painel "Diagnóstico operacional e prescrição AIOps"
da apresentação.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def diagnostico_por_equipe(df: pd.DataFrame) -> pd.DataFrame:
    viol = df[df["KPI Violado?"] == "SIM"]
    total_by_team = df.groupby("Grupo designado").size().rename("total_chamados")
    viol_by_team = viol.groupby("Grupo designado").size().rename("violacoes_ola")

    out = pd.concat([total_by_team, viol_by_team], axis=1).fillna(0)
    out["violacoes_ola"] = out["violacoes_ola"].astype(int)
    out["taxa_violacao_pct"] = np.round(
        np.where(out["total_chamados"] > 0, 100 * out["violacoes_ola"] / out["total_chamados"], 0), 3
    )
    out = out.sort_values("violacoes_ola", ascending=False).reset_index()
    out["pct_do_total_violacoes"] = np.round(
        100 * out["violacoes_ola"] / max(int(viol_by_team.sum()), 1), 1
    )
    return out


def diagnostico_por_produto(df: pd.DataFrame) -> pd.DataFrame:
    work = df[df["Produto"].notna()].copy()
    is_p2p3 = work["Prioridade"].isin(config.FORECAST_PRIORITIES)
    viol = work["KPI Violado?"] == "SIM"

    out = (
        work.assign(is_p2p3=is_p2p3, viol=viol)
        .groupby("Produto")
        .agg(
            total_chamados=("Número", "count"),
            incidentes_p2p3=("is_p2p3", "sum"),
            violacoes_ola=("viol", "sum"),
        )
        .reset_index()
        .sort_values("incidentes_p2p3", ascending=False)
    )
    return out


def diagnostico_por_ativo(df: pd.DataFrame, min_incidentes: int = None) -> pd.DataFrame:
    min_incidentes = min_incidentes or config.MIN_INCIDENTS_PER_CONFIG_ITEM
    work = df[df["Item de configuração"].notna()].copy()
    viol = work["KPI Violado?"] == "SIM"

    out = (
        work.assign(viol=viol)
        .groupby("Item de configuração")
        .agg(total_chamados=("Número", "count"), violacoes_ola=("viol", "sum"))
        .reset_index()
    )
    out = out[out["total_chamados"] >= min_incidentes].copy()
    out["taxa_violacao_pct"] = np.round(100 * out["violacoes_ola"] / out["total_chamados"], 2)
    out = out.sort_values("taxa_violacao_pct", ascending=False).reset_index(drop=True)
    return out


def janela_critica_de_violacoes(df: pd.DataFrame) -> pd.DataFrame:
    """Identifica, a partir dos dados reais, dia da semana x faixa de horário
    com maior concentração de violações de OLA — para orientar a redistribuição
    de escalas (equivalente ao achado 'terças a quintas, 9h-17h' da Sprint 3)."""
    viol = df[df["KPI Violado?"] == "SIM"].copy()
    if viol.empty:
        return pd.DataFrame(columns=["dia_semana", "faixa_horaria", "violacoes_ola"])

    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    viol["dia_semana_nome"] = viol["Aberto"].dt.dayofweek.map(lambda d: dias[d])
    viol["faixa_horaria"] = pd.cut(
        viol["Aberto"].dt.hour,
        bins=[-1, 5, 11, 17, 23],
        labels=["Madrugada (0-5h)", "Manhã (6-11h)", "Tarde (12-17h)", "Noite (18-23h)"],
    )
    out = (
        viol.groupby(["dia_semana_nome", "faixa_horaria"], observed=True)
        .size()
        .rename("violacoes_ola")
        .reset_index()
        .sort_values("violacoes_ola", ascending=False)
    )
    return out


def _kpi_attainment(qtd: int, tabela: list[tuple[float, float, float]]) -> float:
    for lo, hi, pct in tabela:
        if lo <= qtd <= hi:
            return pct
    return 0.0


def tabela_metas_kpi(df: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Compara o realizado do ano com as metas anuais do Dicionário de Dados v2."""
    work = df[df["Aberto"].dt.year == ano]
    rows = []
    for prioridade in ["2 - Alta", "3 - Média"]:
        subset = work[work["Prioridade"] == prioridade]
        qtd_viol = int((subset["KPI Violado?"] == "SIM").sum())
        qtd_total = int(subset["Entrou para KPI?"].eq("SIM").sum())

        pct_viol = _kpi_attainment(qtd_viol, config.METAS_QUEBRA_OLA[prioridade])
        pct_vol = _kpi_attainment(qtd_total, config.METAS_VOLUME_TOTAL[prioridade])

        rows.append({
            "ano": ano, "prioridade": prioridade, "indicador": "Incidentes com OLA quebrado",
            "realizado": qtd_viol, "pct_atingimento_meta": pct_viol,
        })
        rows.append({
            "ano": ano, "prioridade": prioridade, "indicador": "Volume total de incidentes tratados",
            "realizado": qtd_total, "pct_atingimento_meta": pct_vol,
        })
    return pd.DataFrame(rows)


def gerar_recomendacoes(equipe_df: pd.DataFrame, ativo_df: pd.DataFrame, janela_df: pd.DataFrame) -> pd.DataFrame:
    """Consolida a matriz de recomendações prescritivas usada no dashboard."""
    recomendacoes = []

    for _, row in equipe_df.head(3).iterrows():
        if row["violacoes_ola"] == 0:
            continue
        recomendacoes.append({
            "categoria": "Equipe",
            "alvo": row["Grupo designado"],
            "indicador": f"{int(row['violacoes_ola'])} violações de OLA ({row['pct_do_total_violacoes']}% do total)",
            "acao_recomendada": "Revisar dimensionamento da equipe e abrir Problem Records para as causas recorrentes.",
        })

    for _, row in ativo_df.head(3).iterrows():
        recomendacoes.append({
            "categoria": "Ativo (Item de Configuração)",
            "alvo": row["Item de configuração"],
            "indicador": f"Taxa de violação de {row['taxa_violacao_pct']}% em {int(row['total_chamados'])} chamados",
            "acao_recomendada": "Investigar instabilidade crônica do ativo; priorizar saneamento estrutural.",
        })

    if not janela_df.empty:
        top_janela = janela_df.iloc[0]
        recomendacoes.append({
            "categoria": "Escala / Janela crítica",
            "alvo": f"{top_janela['dia_semana_nome']} — {top_janela['faixa_horaria']}",
            "indicador": f"{int(top_janela['violacoes_ola'])} violações concentradas nesta janela",
            "acao_recomendada": "Redistribuir escalas de plantão para reforçar cobertura nesse período.",
        })

    return pd.DataFrame(recomendacoes)
