"""
Fetcher de dados para o módulo network_analyst.
Consome os endpoints /frentes, /frentes/{id}/membros e /deputados da API da Câmara.
"""

import time
import requests
from typing import Optional

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "SistemaCamaraAnalise/1.0",
}
TIMEOUT = 30
ITEMS_POR_PAGINA = 100


def get_frentes(legislatura: Optional[int] = None) -> list[dict]:
    """
    Retorna lista de frentes parlamentares ativas.

    Args:
        legislatura: Número da legislatura (ex: 57). Se None, retorna a atual.

    Returns:
        Lista de frentes com id, titulo e uri.
    """
    url = f"{BASE_URL}/frentes"
    params = {"itens": ITEMS_POR_PAGINA}
    if legislatura:
        params["idLegislatura"] = legislatura

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        frentes = response.json().get("dados", [])
        print(f"[network_analyst] {len(frentes)} frentes parlamentares obtidas.")
        return frentes
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao buscar frentes: {e}")
        return []


def get_membros_frente(frente_id: int) -> list[dict]:
    """
    Retorna os membros (deputados) de uma frente parlamentar específica.

    Args:
        frente_id: ID da frente parlamentar.

    Returns:
        Lista de deputados membros da frente.
    """
    url = f"{BASE_URL}/frentes/{frente_id}/membros"
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json().get("dados", [])
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao buscar membros da frente {frente_id}: {e}")
        return []


def get_deputados(legislatura: Optional[int] = None) -> list[dict]:
    """
    Retorna lista completa de deputados com informações básicas.

    Args:
        legislatura: Número da legislatura (ex: 57).

    Returns:
        Lista de deputados com id, nome, partido e UF.
    """
    url = f"{BASE_URL}/deputados"
    params = {"itens": ITEMS_POR_PAGINA, "ordem": "ASC", "ordenarPor": "nome"}
    if legislatura:
        params["idLegislatura"] = legislatura

    all_deputados = []
    pagina = 1

    while True:
        params["pagina"] = pagina
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[ERRO] Falha ao buscar deputados (pág. {pagina}): {e}")
            break

        dados = response.json()
        registros = dados.get("dados", [])
        if not registros:
            break

        all_deputados.extend(registros)

        links = dados.get("links", [])
        proxima = next((l for l in links if l.get("rel") == "next"), None)
        if not proxima:
            break

        pagina += 1
        time.sleep(0.3)

    print(f"[network_analyst] {len(all_deputados)} deputados obtidos.")
    return all_deputados


def build_frente_deputado_map(frentes: list[dict], delay: float = 0.5) -> dict[int, list[dict]]:
    """
    Constrói mapa: {frente_id → [lista de deputados membros]}.
    Faz requisições individuais por frente com delay para respeitar a API.

    Args:
        frentes: Lista de frentes obtida via get_frentes().
        delay: Pausa em segundos entre requisições à API.

    Returns:
        Dicionário mapeando IDs de frentes a sus membros.
    """
    mapa: dict[int, list[dict]] = {}
    total = len(frentes)

    for i, frente in enumerate(frentes):
        fid = frente.get("id")
        if not fid:
            continue
        membros = get_membros_frente(fid)
        mapa[fid] = membros
        print(f"  [{i+1}/{total}] Frente {fid}: {len(membros)} membros")
        time.sleep(delay)

    return mapa
