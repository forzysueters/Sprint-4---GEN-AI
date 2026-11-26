"""Configuração central do assistente Forzy (caminhos e variáveis de ambiente)."""
import os
from pathlib import Path

RAIZ = Path(os.getenv("FORZY_BASE_DIR", Path(__file__).resolve().parent.parent))

# Carrega um arquivo .env simples (CHAVE=valor), sem sobrescrever variáveis já exportadas
_env = RAIZ / ".env"
if _env.exists():
    for _linha in _env.read_text(encoding="utf-8").splitlines():
        _linha = _linha.split("#", 1)[0].strip()
        if "=" in _linha:
            _k, _v = (x.strip() for x in _linha.split("=", 1))
            if _v:
                os.environ.setdefault(_k, _v)

# Artefatos das sprints anteriores
MOTOR_DB = RAIZ / "sprint2" / "motor.db"
MODELO_FALHAS = RAIZ / "sprint2" / "modelo_falhas.joblib"
MODELO_ISO = RAIZ / "sprint3" / "modelo_anomalias_isoforest.joblib"
MODELO_AE = RAIZ / "sprint3" / "modelo_autoencoder.pt"
SCORES_FZ = RAIZ / "sprint3" / "scores_anomalias.csv"
BASELINE_FZ = RAIZ / "sprint3" / "baseline_operacional.json"

# Base de conhecimento do RAG
DIR_DOCS = RAIZ / "conhecimento" / "documentos"
DIR_GERADO = RAIZ / "conhecimento" / "gerado"
HISTORICO_OS = RAIZ / "conhecimento" / "historico_manutencao.csv"
INDICE = RAIZ / "indice" / "indice_rag.joblib"

# Parâmetros do RAG e do LLM
TOP_K = int(os.getenv("RAG_TOP_K", "4"))
MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.12"))
LLM_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
USAR_LLM = os.getenv("FORZY_MODO", "auto")  # auto | llm | offline

ID_FORZY = "FZ-ATV-01"
IDS_MOTORES = [f"MTR-{i:02d}" for i in range(1, 21)]
