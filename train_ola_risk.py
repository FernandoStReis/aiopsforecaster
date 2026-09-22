"""
Classificador de risco de quebra de OLA + explicabilidade (XAI).

Prevê, para cada chamado elegível ao KPI, a probabilidade de o OLA ser
violado (campo `KPI Violado? = SIM`). O problema é fortemente
desbalanceado (poucas violações no universo de chamados elegíveis), por
isso o modelo usa `class_weight="balanced"`, como descrito na Sprint 3
("Random Forest balanceado").

Saídas:
- métricas de discriminação (ROC-AUC via validação cruzada estratificada)
- probabilidade de risco por chamado (para popular alertas no dashboard)
- importância das features (para o painel de explicabilidade / XAI)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from . import config

FEATURE_COLS = [
    "prioridade_ordinal", "grupo_designado_freq", "item_configuracao_freq",
    "produto_freq", "categoria_freq", "dia_semana", "is_weekend",
    "is_noturno", "is_troca_turno", "hora_abertura",
]

# Rótulos amigáveis para o painel de explicabilidade (mapeiam 1:1 com FEATURE_COLS)
FEATURE_LABELS = {
    "prioridade_ordinal": "Prioridade do chamado",
    "grupo_designado_freq": "Grupo designado",
    "item_configuracao_freq": "Item de configuração (frequência)",
    "produto_freq": "Produto (frequência)",
    "categoria_freq": "Categoria (frequência)",
    "dia_semana": "Dia da semana",
    "is_weekend": "Aberto em fim de semana",
    "is_noturno": "Janela de abertura (noturno)",
    "is_troca_turno": "Janela de abertura (troca de turno)",
    "hora_abertura": "Hora de abertura",
}


def _make_model() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=400,
        max_depth=8,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=config.RANDOM_STATE,
        n_jobs=-1,
    )


def train_and_score(tickets: pd.DataFrame) -> dict:
    """
    Roda a validação cruzada estratificada para estimar o ROC-AUC de forma
    honesta, treina o modelo final em 100% dos dados e calcula as
    probabilidades de risco + importância das features.

    O ROC-AUC (e a curva ROC) são calculados aqui, em Python — é uma métrica
    que exige varrer todos os limiares de decisão e integrar a área sob a
    curva, algo que o Looker Studio não tem como função nativa. O Looker
    Studio só precisa EXIBIR o resultado já calculado (ver `roc_curve` e
    `metrics["roc_auc_cv"]` no retorno).
    """
    from sklearn.metrics import roc_auc_score, roc_curve

    X = tickets[FEATURE_COLS]
    y = tickets["kpi_violado"].values

    n_splits = 5 if y.sum() >= 5 else max(2, int(y.sum()))
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=config.RANDOM_STATE)

    cv_model = _make_model()
    oof_proba = cross_val_predict(cv_model, X, y, cv=skf, method="predict_proba")[:, 1]
    roc_auc_cv = roc_auc_score(y, oof_proba)

    # Pontos da curva ROC (taxa de falso positivo x taxa de verdadeiro
    # positivo, em cada limiar de decisão) a partir das previsões
    # out-of-fold da validação cruzada — prontos para virar um gráfico de
    # linha no Looker Studio (eixo X = fpr, eixo Y = tpr).
    fpr, tpr, thresholds = roc_curve(y, oof_proba)
    roc_curve_df = pd.DataFrame({
        "fpr": np.round(fpr, 4),
        "tpr": np.round(tpr, 4),
        "limiar": np.round(np.clip(thresholds, 0, 1), 4),
        "tpr_classificador_aleatorio": np.round(fpr, 4),  # linha de referência (diagonal)
    })

    final_model = _make_model()
    final_model.fit(X, y)
    proba_full = final_model.predict_proba(X)[:, 1]

    importances = pd.Series(final_model.feature_importances_, index=FEATURE_COLS)
    importances = importances.sort_values(ascending=False)
    importance_df = pd.DataFrame({
        "feature": importances.index,
        "fator": [FEATURE_LABELS.get(f, f) for f in importances.index],
        "importancia_pct": np.round(importances.values * 100, 2),
    })

    predictions = tickets[["Número", "Aberto", "Grupo designado", "Produto", "Item de configuração"]].copy()
    predictions["probabilidade_risco_ola"] = np.round(proba_full, 4)
    predictions["risco_alto"] = (predictions["probabilidade_risco_ola"] >= 0.5).astype(int)
    predictions["kpi_violado_real"] = tickets["kpi_violado"].values
    predictions = predictions.sort_values("probabilidade_risco_ola", ascending=False).reset_index(drop=True)

    metrics = {
        "n_chamados_elegiveis": int(len(tickets)),
        "n_violacoes": int(y.sum()),
        "taxa_violacao_pct": round(100 * y.sum() / len(y), 3),
        "roc_auc_cv": round(float(roc_auc_cv), 4),
        "n_splits_cv": n_splits,
        "modelo": "RandomForestClassifier (class_weight=balanced)",
    }

    return {
        "metrics": metrics,
        "predictions": predictions,
        "feature_importance": importance_df,
        "roc_curve": roc_curve_df,
        "model": final_model,
    }
