"""
Modelagem preditiva de volume de incidentes — D+1 e D+7.

- D+1: volume total de chamados previsto para o dia seguinte.
- D+7: carga da semana seguinte (soma dos próximos 7 dias), usada para
  planejamento de escalas de plantão, como descrito na Sprint 3.

Métrica principal: WAPE (Weighted Absolute Percentage Error), a mesma
usada nas apresentações anteriores do projeto, complementada por MAE.

O modelo tenta usar XGBoost (citado na Sprint 2/3 como uma das opções de
ML). Se a biblioteca não estiver disponível no ambiente de quem for
rodar o pipeline, cai automaticamente para o HistGradientBoostingRegressor
do scikit-learn, que não exige dependências externas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from . import config

try:
    from xgboost import XGBRegressor
    _HAS_XGBOOST = True
except ImportError:  # pragma: no cover - ambiente sem xgboost instalado
    _HAS_XGBOOST = False


FEATURE_COLS_BASE = [
    "dia_semana", "is_weekend", "is_month_start", "is_month_end",
]


def _make_model():
    if _HAS_XGBOOST:
        return XGBRegressor(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=config.RANDOM_STATE,
            objective="reg:squarederror",
        )
    return HistGradientBoostingRegressor(
        max_depth=4,
        learning_rate=0.05,
        random_state=config.RANDOM_STATE,
    )


def _wape(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true)) * 100)


def _mae(y_true, y_pred) -> float:
    return float(np.mean(np.abs(np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float))))


def _feature_cols_for(target_col: str) -> list[str]:
    return FEATURE_COLS_BASE + [
        c for c in [
            f"{target_col}_lag1", f"{target_col}_lag2", f"{target_col}_lag3",
            f"{target_col}_lag7", f"{target_col}_lag14",
            f"{target_col}_roll_mean_7", f"{target_col}_roll_std_7",
        ]
    ]


def train_and_forecast_d1(daily: pd.DataFrame, target_col: str = "volume_total") -> dict:
    """Treina e avalia o modelo D+1 com validação temporal (últimos N dias como teste)."""
    feats = _feature_cols_for(target_col)
    data = daily.dropna(subset=feats).reset_index(drop=True)

    n_test = min(config.N_TEST_DAYS_D1, max(1, len(data) // 4))
    train, test = data.iloc[:-n_test], data.iloc[-n_test:]

    model = _make_model()
    model.fit(train[feats], train[target_col])

    pred_train = model.predict(train[feats])
    pred_test = model.predict(test[feats])

    metrics = {
        "target": target_col,
        "horizon": "D+1",
        "modelo": "XGBoost" if _HAS_XGBOOST else "HistGradientBoosting (fallback)",
        "wape_treino_pct": round(_wape(train[target_col], pred_train), 2),
        "wape_teste_pct": round(_wape(test[target_col], pred_test), 2),
        "mae_treino": round(_mae(train[target_col], pred_train), 1),
        "mae_teste": round(_mae(test[target_col], pred_test), 1),
        "n_dias_treino": len(train),
        "n_dias_teste": len(test),
    }

    forecast_df = test[["data", target_col]].copy()
    forecast_df = forecast_df.rename(columns={target_col: "valor_real"})
    forecast_df["valor_previsto"] = np.round(pred_test).astype(int)
    forecast_df["horizonte"] = "D+1"
    forecast_df["target"] = target_col

    return {"metrics": metrics, "forecast": forecast_df, "model": model, "features": feats}


def train_and_forecast_d7(daily: pd.DataFrame, target_col: str = "volume_total") -> dict:
    """
    Treina o modelo D+7: prevê a soma de volume dos PRÓXIMOS 7 dias a partir
    das features conhecidas no dia t (carga semanal projetada).
    """
    feats = _feature_cols_for(target_col)
    data = daily.dropna(subset=feats).copy()

    # Alvo: soma dos próximos 7 dias (t+1 .. t+7)
    future_sum = data[target_col].iloc[::-1].rolling(7).sum().iloc[::-1].shift(-1)
    data["target_d7"] = future_sum
    data = data.dropna(subset=["target_d7"]).reset_index(drop=True)

    n_test = min(config.N_TEST_DAYS_D1, max(1, len(data) // 4))
    train, test = data.iloc[:-n_test], data.iloc[-n_test:]

    model = _make_model()
    model.fit(train[feats], train["target_d7"])

    pred_train = model.predict(train[feats])
    pred_test = model.predict(test[feats])

    metrics = {
        "target": target_col,
        "horizon": "D+7",
        "modelo": "XGBoost" if _HAS_XGBOOST else "HistGradientBoosting (fallback)",
        "wape_treino_pct": round(_wape(train["target_d7"], pred_train), 2),
        "wape_teste_pct": round(_wape(test["target_d7"], pred_test), 2),
        "mae_treino": round(_mae(train["target_d7"], pred_train), 1),
        "mae_teste": round(_mae(test["target_d7"], pred_test), 1),
        "n_dias_treino": len(train),
        "n_dias_teste": len(test),
    }

    forecast_df = test[["data", "target_d7"]].copy()
    forecast_df = forecast_df.rename(columns={"target_d7": "valor_real"})
    forecast_df["valor_previsto"] = np.round(pred_test).astype(int)
    forecast_df["horizonte"] = "D+7"
    forecast_df["target"] = target_col

    return {"metrics": metrics, "forecast": forecast_df, "model": model, "features": feats}
