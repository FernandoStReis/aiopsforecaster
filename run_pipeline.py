"""
Orquestrador do pipeline AIOps Forecaster.

Executa, em sequência:
1. Carga e limpeza do dataset de incidentes.
2. Engenharia da série diária de volume (com lags/médias móveis).
3. Treino e avaliação dos modelos de previsão de volume (D+1 e D+7).
4. Treino do classificador de risco de quebra de OLA + XAI.
5. Diagnóstico operacional e geração da matriz de recomendações.
6. Exportação de todos os artefatos, prontos para servir de fonte de
   dados ao dashboard no Looker Studio (via Google Sheets ou BigQuery).

Uso:
    python -m src.run_pipeline
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

if __package__ in (None, ""):
    # Permite rodar como `python src/run_pipeline.py` além de `python -m src.run_pipeline`
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from src import config, data_prep, diagnostics, train_ola_risk, train_volume_forecast
else:
    from . import config, data_prep, diagnostics, train_ola_risk, train_volume_forecast


def _save_csv(df: pd.DataFrame, name: str) -> Path:
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = config.OUTPUT_DIR / name
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"  -> {out_path.relative_to(config.BASE_DIR)}  ({len(df)} linhas)")
    return out_path


def main() -> None:
    print("=" * 70)
    print("AIOps Forecaster — pipeline de geração dos outputs do dashboard")
    print("=" * 70)

    print("\n[1/6] Carregando e limpando o dataset bruto...")
    raw = data_prep.load_raw_dataset()
    print(f"  Total de chamados carregados: {len(raw):,}".replace(",", "."))

    print("\n[2/6] Construindo a série diária de volume (com lags e calendário)...")
    daily_full = data_prep.build_daily_volume_table(raw)
    daily_regime, daily_with_warmup = data_prep.restrict_to_current_regime(daily_full)
    print(
        f"  Regime atual considerado a partir de {config.REGIME_BREAK_DATE} "
        f"({len(daily_regime)} dias, {daily_regime['volume_total'].sum():,} chamados)".replace(",", ".")
    )
    _save_csv(
        daily_full[["data", "volume_total", "volume_p2p3", "volume_kpi_elegivel", "volume_kpi_violado"]],
        "fato_incidentes_diario.csv",
    )

    print("\n[3/6] Treinando modelos de previsão de volume (D+1 e D+7)...")
    all_metrics = []
    all_forecasts = []
    for target_col in ["volume_total", "volume_p2p3"]:
        d1 = train_volume_forecast.train_and_forecast_d1(daily_with_warmup, target_col)
        d7 = train_volume_forecast.train_and_forecast_d7(daily_with_warmup, target_col)
        all_metrics += [d1["metrics"], d7["metrics"]]
        all_forecasts += [d1["forecast"], d7["forecast"]]
        print(
            f"  {target_col:14s} D+1 -> WAPE teste {d1['metrics']['wape_teste_pct']}% "
            f"| D+7 -> WAPE teste {d7['metrics']['wape_teste_pct']}%"
        )

    _save_csv(pd.DataFrame(all_metrics), "metricas_modelos_previsao_volume.csv")
    _save_csv(pd.concat(all_forecasts, ignore_index=True), "previsao_volume_d1_d7.csv")

    print("\n[4/6] Treinando o classificador de risco de quebra de OLA (XAI)...")
    tickets = data_prep.build_ticket_level_table(raw)
    risk_result = train_ola_risk.train_and_score(tickets)
    print(
        f"  Chamados elegíveis ao KPI: {risk_result['metrics']['n_chamados_elegiveis']:,} | "
        f"Violações: {risk_result['metrics']['n_violacoes']} "
        f"({risk_result['metrics']['taxa_violacao_pct']}%)".replace(",", ".")
    )
    print(f"  ROC-AUC (validação cruzada): {risk_result['metrics']['roc_auc_cv']}")

    _save_csv(pd.DataFrame([risk_result["metrics"]]), "metricas_classificador_risco_ola.csv")
    _save_csv(risk_result["predictions"], "risco_ola_por_chamado.csv")
    _save_csv(risk_result["feature_importance"], "feature_importance_risco_ola.csv")
    _save_csv(risk_result["roc_curve"], "curva_roc_risco_ola.csv")

    print("\n[5/6] Gerando diagnóstico operacional e recomendações prescritivas...")
    equipe_df = diagnostics.diagnostico_por_equipe(raw)
    produto_df = diagnostics.diagnostico_por_produto(raw)
    ativo_df = diagnostics.diagnostico_por_ativo(raw)
    janela_df = diagnostics.janela_critica_de_violacoes(raw)
    recomendacoes_df = diagnostics.gerar_recomendacoes(equipe_df, ativo_df, janela_df)

    _save_csv(equipe_df, "diagnostico_por_equipe.csv")
    _save_csv(produto_df, "diagnostico_por_produto.csv")
    _save_csv(ativo_df, "diagnostico_por_ativo.csv")
    _save_csv(janela_df, "janela_critica_violacoes.csv")
    _save_csv(recomendacoes_df, "recomendacoes_prescritivas.csv")

    print("\n[6/6] Gerando tabela de atingimento das metas anuais de KPI...")
    metas_frames = [
        diagnostics.tabela_metas_kpi(raw, ano)
        for ano in sorted(raw["Aberto"].dt.year.dropna().unique().astype(int))
    ]
    _save_csv(pd.concat(metas_frames, ignore_index=True), "atingimento_metas_kpi_anual.csv")

    summary = {
        "chamados_processados": int(len(raw)),
        "periodo": [str(raw["Aberto"].min().date()), str(raw["Aberto"].max().date())],
        "regime_atual_desde": config.REGIME_BREAK_DATE,
        "modelos_volume": all_metrics,
        "classificador_risco_ola": risk_result["metrics"],
    }
    with open(config.OUTPUT_DIR / "resumo_execucao.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\nConcluído! Todos os arquivos foram gravados em:")
    print(f"  {config.OUTPUT_DIR}")
    print("\nEsses CSVs podem ser publicados no Google Sheets ou carregados em")
    print("uma tabela do BigQuery para servirem de fonte de dados ao Looker Studio.")


if __name__ == "__main__":
    main()
