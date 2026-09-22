# AIOps Forecaster

**Predictive operations intelligence for IT incident management**
FIAP × Locaweb Enterprise Challenge — 2TSCOA · Group 18 · 2026

AIOps Forecaster turns raw ITSM incident data into forward-looking operational
intelligence. It forecasts incident volume for the next day (D+1) and the
next week (D+7), classifies the risk of breaching Operational Level
Agreements (OLA) with an explainable model, and surfaces prescriptive
recommendations by team, product, and configuration item — helping Locaweb's
operations move from reactive firefighting to proactive planning.

---

## Table of contents

- [Business context](#business-context)
- [Objectives](#objectives)
- [Solution architecture](#solution-architecture)
- [Repository structure](#repository-structure)
- [Dataset](#dataset)
- [Getting started](#getting-started)
- [Pipeline modules](#pipeline-modules)
- [Results](#results)
- [Dashboard](#dashboard)
- [Video pitch](#video-pitch)
- [Team](#team)
- [Acknowledgments](#acknowledgments)
- [License](#license)

---

## Business context

Locaweb runs a large-scale, 24/7 technology operation. Incidents are logged
continuously in an ITSM platform, and today the operations team is largely
**reactive** — acting only after a failure has already occurred. In a
dynamic environment with recurring failures, this creates a real risk of
breaching OLAs (Operational Level Agreements) and destabilizes service
availability.

## Objectives

The challenge asked groups to propose a solution that:

1. **Anticipates incidents** — forecast incident volume for D+1 and D+7,
   broken down by priority (P2/P3 mandatory).
2. **Identifies trends** — daily volume trend and OLA-loss risk trend.
3. **Projects KPI impact** — probability of hitting the annual OLA and
   volume targets.
4. **Supports operational decisions** — points to where to act
   preventively: team, product, or configuration item.

## Solution architecture

**Reference architecture (target for production):** a fully managed Google
Cloud Platform stack — Cloud Storage + Cloud Composer (Airflow) for
ingestion, BigQuery as the data warehouse, Vertex AI for model training
(XGBoost / Random Forest), and Looker Studio for visualization.

**What is actually implemented in this repository:** the academic
environment does not provide paid cloud access, so this repo implements the
**same pipeline logic** with a lightweight, zero-cost, fully reproducible
stack:

| Layer | Reference (production) | Implemented here |
|---|---|---|
| Ingestion / ETL | Cloud Composer (Airflow) | Local Python scripts (`src/data_prep.py`) |
| Storage | BigQuery | Local CSV / pandas DataFrames |
| Modeling | Vertex AI (XGBoost / Random Forest) | scikit-learn + XGBoost, run locally |
| Visualization | Looker Studio | Looker Studio, fed by Google Sheets (CSV exports) |

This is an honest, working MVP: the models are trained on the real dataset
end-to-end, not simulated — only the cloud infrastructure layer is
conceptual.

## Repository structure

```
aiops-forecaster/
├── README.md                      <- this file
├── LICENSE
├── requirements.txt
├── data/
│   └── LW-DATASET.xlsx            <- raw incident dataset (see Dataset section)
├── src/
│   ├── config.py                  <- paths, business rules, KPI targets
│   ├── data_prep.py                <- load, clean, feature engineering
│   ├── train_volume_forecast.py    <- D+1 / D+7 volume forecasting models
│   ├── train_ola_risk.py           <- OLA breach risk classifier + XAI
│   ├── diagnostics.py               <- team/product/asset diagnostics + recommendations
│   └── run_pipeline.py             <- orchestrates the full pipeline
├── outputs/                        <- generated CSVs, ready for Looker Studio
├── docs/
│   ├── Dicionario_de_Dados_v2.docx  <- data dictionary
│   └── EC_Sprint_4_2TSCOA_solucaofinal_AIOpsForecaster_Grupo18.pptx
└── video/
    ├── Roteiro_Video_Pitch.md      <- pitch video script
    └── link_video_pitch.txt        <- public YouTube link + team/RM info
```

## Dataset

The dataset (`data/LW-DATASET.xlsx`) contains **122,543 IT incidents**
logged between 2023 and 2025, with fields such as priority, product,
category, assigned team, configuration item, open/resolve/close timestamps,
duration, and OLA compliance flags. The full field-by-field description is
in `docs/Dicionario_de_Dados_v2.docx`.

> **Confidentiality note:** this dataset contains real operational data
> shared by a corporate partner (Locaweb) for academic purposes only. If
> this repository is public, confirm with your course instructor whether
> the raw file should stay in the repo or be limited to the private
> submission package.

## Getting started

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.run_pipeline
```

The script prints progress for each stage and writes all final artifacts to
`outputs/`. If `xgboost` isn't available in the runtime, the pipeline
automatically falls back to scikit-learn's `HistGradientBoostingRegressor` —
no step breaks due to that optional dependency.

## Pipeline modules

| Module | Responsibility |
|---|---|
| `src/config.py` | Paths, business rules, and KPI targets (from the Data Dictionary v2) |
| `src/data_prep.py` | Excel loading, cleaning, calendar/lag/frequency feature engineering |
| `src/train_volume_forecast.py` | D+1 (next day) and D+7 (next-week load) volume forecasting |
| `src/train_ola_risk.py` | OLA breach risk classifier (balanced Random Forest) + feature importance |
| `src/diagnostics.py` | Team/product/asset diagnostics, critical time-window detection, prescriptive matrix |
| `src/run_pipeline.py` | Orchestrates all stages and exports the final CSVs |

Key modeling decisions — regime break handling (a monitoring-automation
rollout from Sept/2025 caused a volume step-change), the D+7 definition
(forward 7-day sum, not a single point forecast), and the frequency-encoding
approach used for explainability — are documented as comments in the
corresponding modules.

## Results

Metrics obtained by running this pipeline end-to-end against the real
dataset (see `outputs/resumo_execucao.json` for the latest run):

| Model | Metric | Result |
|---|---|---|
| Volume forecast — D+1 (total) | WAPE (test) | ~18.1% |
| Volume forecast — D+7 (weekly load, total) | WAPE (test) | ~19.6% |
| OLA breach risk classifier | ROC-AUC (5-fold stratified CV) | ~0.81 |
| OLA breach risk classifier | Violation rate in eligible tickets | ~0.97% |

Top diagnostic findings (fully reproducible from `outputs/diagnostico_*.csv`):
Team11 and Team09 concentrate the majority of 2025 OLA violations, and
configuration item `IC00840` shows a chronically high violation rate,
flagging it as a priority for structural remediation.

## Dashboard

Live Looker Studio dashboard: **[LINK DO DASHBOARD / LOOKER STUDIO]**

Built directly from the CSVs in `outputs/`, published through Google
Sheets. Pages: Overview, Volume Forecast (D+1/D+7), OLA Risk & Explainability,
and Operational Diagnostics & Recommendations.

## Video pitch

Public pitch video (YouTube): **[LINK DO VÍDEO NO YOUTUBE]**
(also available in `video/link_video_pitch.txt`, per submission rules)

## Team

FIAP · 2TSCOA · Group 18 (alphabetical order, as required by the challenge rules)

| Name | RM |
|---|---|
| Fernando Santos Reis | 562410 |
| Leonardo Breyer | 563568 |
| Leonardo Lourenço | 562825 |

## Acknowledgments

Built for the **FIAP × Locaweb Enterprise Challenge** (2TSCOA, 2026), across
Sprints 1–4. Thanks to Locaweb and the course staff for the dataset, the
mentorship, and the opportunity to work on a real operational problem.

## License

This project is licensed under the [MIT License](LICENSE) — see the
`LICENSE` file for details. The dataset in `data/` is not covered by this
license; see the confidentiality note above.
:)
