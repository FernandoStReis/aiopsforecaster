"""
Configurações e constantes do pipeline AIOps Forecaster.

Centraliza caminhos, nomes de colunas e as regras de negócio descritas
no "Dicionário de Dados - v2" do Enterprise Challenge Locaweb, para que
os demais módulos não precisem repetir esses números mágicos.
"""
from pathlib import Path

# --------------------------------------------------------------------------
# Caminhos
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

RAW_DATASET_PATH = DATA_DIR / "LW-DATASET.xlsx"
RAW_DATASET_SHEET = "Dataset Geral"

# --------------------------------------------------------------------------
# Regra de negócio: quebra de regime operacional
# --------------------------------------------------------------------------
# A partir de setembro/2025 houve um salto volumétrico gerado pela automação
# do monitoramento (identificado na Sprint 3: ~85% dos chamados do dataset
# ocorrem a partir dessa data). Para que os modelos de série temporal não
# aprendam um padrão que não existe mais na operação atual, o pipeline treina
# e avalia a previsão de volume apenas no regime "pós-automação".
REGIME_BREAK_DATE = "2025-09-01"

# Quantos dias de warm-up antes da quebra de regime são usados só para
# calcular lags/médias móveis do primeiro dia útil do novo regime.
WARMUP_DAYS = 14

# --------------------------------------------------------------------------
# Prioridades que entram no cálculo de KPI, por regra do Dicionário de Dados
# --------------------------------------------------------------------------
KPI_PRIORITIES = ["1 - Crítica", "2 - Alta", "3 - Média"]
FORECAST_PRIORITIES = ["2 - Alta", "3 - Média"]  # P2/P3, obrigatórias no desafio

# Duração máxima (em horas) permitida por prioridade antes de violar o OLA
SLA_HOURS_BY_PRIORITY = {
    "1 - Crítica": 4,
    "2 - Alta": 4,
    "3 - Média": 12,
    "4 - Baixa": 24,
    "5 - Muito Baixa": 96,
}

# --------------------------------------------------------------------------
# Metas anuais de KPI (Dicionário de Dados v2) - usadas para a tabela de
# atingimento de metas que alimenta o gauge/indicador no Looker Studio.
# --------------------------------------------------------------------------
METAS_QUEBRA_OLA = {
    "2 - Alta": [
        (0, 30, 150), (31, 35, 125), (36, 39, 100),
        (40, 45, 75), (46, 53, 50), (54, float("inf"), 0),
    ],
    "3 - Média": [
        (0, 200, 150), (201, 230, 125), (231, 263, 100),
        (264, 290, 75), (291, 320, 50), (321, float("inf"), 0),
    ],
}

METAS_VOLUME_TOTAL = {
    "2 - Alta": [
        (0, 4584, 150), (4585, 5388, 125), (5389, 6168, 100),
        (6169, 6252, 75), (6253, 6336, 50), (6337, float("inf"), 0),
    ],
    "3 - Média": [
        (0, 19488, 150), (19489, 22116, 125), (22117, 22524, 100),
        (22525, 23892, 75), (23893, 24276, 50), (24277, float("inf"), 0),
    ],
}

# --------------------------------------------------------------------------
# Modelagem
# --------------------------------------------------------------------------
RANDOM_STATE = 42
N_TEST_DAYS_D1 = 14      # dias finais reservados para avaliar o modelo D+1
MIN_INCIDENTS_PER_CONFIG_ITEM = 20  # amostra mínima para diagnosticar um ativo
