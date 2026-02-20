"""
Fetcher de ementas e textos de proposições legislativas.
Consome o endpoint /proposicoes para extrair textos para análise NLP.
"""

import time
import requests
from typing import Optional

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"Accept": "application/json", "User-Agent": "SistemaCamaraAnalise/1.0"}
TIMEOUT = 30


def get_ementas(
    ano: int,
    tipo_sigla: str = "PL",
    max_paginas: int = 10,
) -> list[str]:
    """
    Extrai ementas de proposições legislativas de um ano específico.

    Args:
        ano: Ano de apresentação das proposições.
        tipo_sigla: Tipo da proposição ('PL', 'PEC', 'MP', etc.).
        max_paginas: Limite de páginas a buscar (100 itens/página).

    Returns:
        Lista de strings com os textos das ementas.
    """
    ementas: list[str] = []
    pagina = 1

    print(f"[tema_miner] Buscando ementas de {tipo_sigla} de {ano}...")

    while pagina <= max_paginas:
        params = {
            "ano": ano,
            "siglaTipo": tipo_sigla,
            "itens": 100,
            "pagina": pagina,
            "ordem": "DESC",
            "ordenarPor": "id",
        }

        try:
            r = requests.get(f"{BASE_URL}/proposicoes", headers=HEADERS, params=params, timeout=TIMEOUT)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[tema_miner] Erro na página {pagina}: {e}")
            break

        dados = r.json()
        registros = dados.get("dados", [])

        if not registros:
            break

        # Extrair apenas ementas não-nulas
        for prop in registros:
            ementa = prop.get("ementa", "")
            if ementa and len(ementa) > 10:
                ementas.append(ementa)

        links = dados.get("links", [])
        if not any(l.get("rel") == "next" for l in links):
            break

        pagina += 1
        time.sleep(0.3)

    print(f"[tema_miner] {len(ementas)} ementas coletadas.")
    return ementas
