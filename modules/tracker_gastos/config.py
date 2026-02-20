"""
Configurações centrais do módulo tracker_gastos.
"""

# URL base da API de Dados Abertos da Câmara dos Deputados
BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

# Headers padrão para requisições
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "SistemaCamaraAnalise/1.0 (projeto educacional)",
}

# Tempo limite para requisições (em segundos)
REQUEST_TIMEOUT = 30

# Itens por página (máximo permitido pela API)
ITEMS_POR_PAGINA = 100

# Diretório de saída dos relatórios
OUTPUT_DIR = "outputs/tracker_gastos"
