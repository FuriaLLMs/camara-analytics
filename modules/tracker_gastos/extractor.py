"""
Extrator de despesas dos deputados via endpoint /deputados/{id}/despesas.
Implementa paginação automática para recuperar todos os registros.
"""

import time
import requests
from typing import Optional

from .config import BASE_URL, HEADERS, REQUEST_TIMEOUT, ITEMS_POR_PAGINA


def get_all_expenses(
    deputado_id: int,
    ano: Optional[int] = None,
    mes: Optional[int] = None,
) -> list[dict]:
    """
    Extrai todas as despesas de um deputado, lidando com paginação automaticamente.

    Args:
        deputado_id: ID do deputado na API da Câmara.
        ano: Filtrar por ano (opcional).
        mes: Filtrar por mês (opcional).

    Returns:
        Lista de dicionários com todas as despesas do deputado.
    """
    url = f"{BASE_URL}/deputados/{deputado_id}/despesas"
    todas_despesas: list[dict] = []
    pagina = 1

    params: dict = {
        "itens": ITEMS_POR_PAGINA,
        "pagina": pagina,
        "ordem": "ASC",
        "ordenarPor": "ano",
    }

    if ano:
        params["ano"] = ano
    if mes:
        params["mes"] = mes

    print(f"[tracker_gastos] Buscando despesas do deputado ID={deputado_id}...")

    while True:
        params["pagina"] = pagina

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"[ERRO HTTP] Página {pagina}: {e}")
            break
        except requests.exceptions.RequestException as e:
            print(f"[ERRO] Falha na requisição: {e}")
            break

        dados = response.json()
        registros = dados.get("dados", [])

        # Se não há registros na página, chegamos ao fim
        if not registros:
            print(f"[tracker_gastos] Paginação concluída na página {pagina}.")
            break

        todas_despesas.extend(registros)
        print(f"  → Página {pagina}: {len(registros)} registros obtidos (total: {len(todas_despesas)})")

        # Verificar se há próxima página via links HATEOAS
        links = dados.get("links", [])
        proxima = next((l for l in links if l.get("rel") == "next"), None)
        if not proxima:
            break

        pagina += 1
        # Pausa breve para não sobrecarregar a API
        time.sleep(0.3)

    print(f"[tracker_gastos] Total de despesas coletadas: {len(todas_despesas)}")
    return todas_despesas


def get_deputados_list(uf: Optional[str] = None, partido: Optional[str] = None) -> list[dict]:
    """
    Lista deputados com filtros opcionais de UF e partido.

    Args:
        uf: Sigla do estado (ex: 'SP', 'RJ').
        partido: Sigla do partido (ex: 'PT', 'PL').

    Returns:
        Lista de deputados.
    """
    url = f"{BASE_URL}/deputados"
    params: dict = {"itens": ITEMS_POR_PAGINA, "ordem": "ASC", "ordenarPor": "nome"}

    if uf:
        params["siglaUf"] = uf
    if partido:
        params["siglaPartido"] = partido

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json().get("dados", [])
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao buscar deputados: {e}")
        return []
