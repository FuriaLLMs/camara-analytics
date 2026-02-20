"""
Configurações do módulo legis_notifier.
Carrega variáveis de ambiente do arquivo .env.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar .env do diretório do módulo
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# API da Câmara
BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "SistemaCamaraAnalise/1.0",
}
REQUEST_TIMEOUT = 30

# Palavras-chave monitoradas (podem ser sobrescritas via .env)
_palavras_raw = os.getenv("PALAVRAS_CHAVE", "educação,saúde,meio ambiente,segurança pública")
PALAVRAS_CHAVE: list[str] = [p.strip() for p in _palavras_raw.split(",")]

# Intervalo de verificação (em segundos)
INTERVALO_SEGUNDOS = int(os.getenv("INTERVALO_SEGUNDOS", "1800"))  # padrão: 30 min

# Arquivo de persistência
PERSISTENCE_FILE = os.path.join(os.path.dirname(__file__), "last_id.json")
