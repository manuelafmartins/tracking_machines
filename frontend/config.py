# frontend/config.py
import os

# Configurações da API
API_URL = "http://127.0.0.1:8000"

# Caminhos para os recursos
DEFAULT_LOGO_PATH = "frontend/images/logo.png"
COMPANY_LOGOS_DIR = "frontend/images/company_logos"

# Garantir que o diretório de logos existe
os.makedirs(COMPANY_LOGOS_DIR, exist_ok=True)