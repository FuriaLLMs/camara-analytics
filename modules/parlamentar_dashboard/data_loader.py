"""
Carregador de dados para o dashboard parlamentar.
Todas as funções usam @st.cache_data para minimizar chamadas à API da Câmara.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import requests
import streamlit as st

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "SistemaCamaraAnalise/1.0 (projeto educacional)",
}
TIMEOUT = 30


def _get(url: str, params: dict | None = None, silent: bool = False) -> dict | None:
    """
    GET helper com tratamento de erros centralizado.

    Args:
        url: URL da requisição.
        params: Parâmetros de query string.
        silent: Se True, suprime warnings na UI (para dados opcionais).

    Returns:
        JSON como dicionário, ou None em caso de erro.
    """
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        if not silent:
            st.warning("⚠️ Sem conexão com a internet. Verifique sua rede.", icon="🌐")
    except requests.exceptions.Timeout:
        if not silent:
            st.warning("⏳ A API da Câmara demorou demais para responder. Tente novamente.", icon="⏱️")
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response else "?"
        if not silent:
            st.warning(f"⚠️ Erro HTTP {code} ao acessar a API da Câmara.", icon="🔴")
    except requests.exceptions.RequestException as e:
        if not silent:
            st.warning(f"⚠️ Erro inesperado: {e}", icon="❌")
    return None


# ── Funções de dados com cache ──────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_deputados(
    uf: Optional[str] = None,
    partido: Optional[str] = None,
) -> list[dict]:
    """
    Busca deputados com filtros opcionais. Cache de 1 hora.

    Args:
        uf: Sigla do estado (ex: 'SP').
        partido: Sigla do partido (ex: 'PT').

    Returns:
        Lista de deputados (vazia em caso de erro).
    """
    params: dict = {"itens": 100, "ordem": "ASC", "ordenarPor": "nome", "pagina": 1}
    if uf:
        params["siglaUf"] = uf
    if partido:
        params["siglaPartido"] = partido

    todos: list[dict] = []
    while True:
        data = _get(f"{BASE_URL}/deputados", params)
        if not data:
            break
        registros = data.get("dados", [])
        if not registros:
            break
        todos.extend(registros)
        links = data.get("links", [])
        if not any(lnk.get("rel") == "next" for lnk in links):
            break
        params = dict(params)
        params["pagina"] = params.get("pagina", 1) + 1

    return todos


@st.cache_data(ttl=3600, show_spinner=False)
def get_deputado_detail(deputado_id: int) -> dict:
    """
    Busca detalhes completos de um deputado (foto, gabinete, etc.). Cache 1h.

    Args:
        deputado_id: ID do deputado na API da Câmara.

    Returns:
        Dicionário com dados do deputado, ou {} em caso de erro.
    """
    data = _get(f"{BASE_URL}/deputados/{deputado_id}")
    return data.get("dados", {}) if data else {}


@st.cache_data(ttl=1800, show_spinner=False)
def get_votacoes(deputado_id: int, ano: int) -> pd.DataFrame:
    """
    Busca votações de um deputado em um ano específico. Cache 30min.

    Args:
        deputado_id: ID do deputado.
        ano: Ano das votações.

    Returns:
        DataFrame com votações, ou DataFrame vazio em caso de erro.
    """
    params = {
        "ano": ano,
        "itens": 100,
        "ordem": "DESC",
        "ordenarPor": "dataVotacao",
    }
    data = _get(f"{BASE_URL}/deputados/{deputado_id}/votacoes", params, silent=True)
    if not data:
        return pd.DataFrame()

    registros = data.get("dados", [])
    return pd.DataFrame(registros) if registros else pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner=False)
def get_despesas(deputado_id: int, ano: int) -> pd.DataFrame:
    """
    Busca todas as despesas CEAP de um deputado com paginação. Cache 30min.

    Args:
        deputado_id: ID do deputado.
        ano: Ano das despesas.

    Returns:
        DataFrame com despesas, ou DataFrame vazio.
    """
    all_data: list[dict] = []
    pagina = 1
    url = f"{BASE_URL}/deputados/{deputado_id}/despesas"
    max_paginas = 20  # Limite de segurança para evitar loop infinito

    while pagina <= max_paginas:
        data = _get(url, {"ano": ano, "itens": 100, "pagina": pagina}, silent=True)
        if not data:
            break

        registros = data.get("dados", [])
        if not registros:
            break

        all_data.extend(registros)

        links = data.get("links", [])
        if not any(lnk.get("rel") == "next" for lnk in links):
            break

        pagina += 1

    return pd.DataFrame(all_data) if all_data else pd.DataFrame()


@st.cache_data(ttl=86400, show_spinner=False)
def get_partidos() -> list[str]:
    """
    Lista de siglas de partidos com representação na Câmara. Cache 24h.

    Returns:
        Lista ordenada de siglas de partidos.
    """
    data = _get(f"{BASE_URL}/partidos", {"itens": 100})
    if not data:
        return []
    return sorted(
        [p["sigla"] for p in data.get("dados", []) if p.get("sigla")]
    )


@st.cache_data(ttl=86400, show_spinner=False)
def get_ufs() -> list[str]:
    """Retorna lista estática de UFs brasileiras. Cache 24h."""
    return [
        "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
        "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
        "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
    ]


def calcular_total_despesas(df: pd.DataFrame) -> float:
    """
    Calcula o total de despesas líquidas de um DataFrame de gastos.

    Args:
        df: DataFrame de despesas da API.

    Returns:
        Soma dos valores líquidos como float.
    """
    if df.empty or "valorLiquido" not in df.columns:
        return 0.0
    return pd.to_numeric(df["valorLiquido"], errors="coerce").fillna(0.0).sum()
