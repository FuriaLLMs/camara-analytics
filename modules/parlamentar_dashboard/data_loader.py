"""
Carregador de dados para o dashboard parlamentar.
Todas as funções usam @st.cache_data para minimizar chamadas à API da Câmara.

Endpoints utilizados (API v2):
- GET /deputados                       → lista paginada
- GET /deputados/{id}                  → detalhe
- GET /deputados/{id}/despesas         → despesas CEAP paginadas
- GET /deputados/{id}/discursos        → discursos em plenário
- GET /deputados/{id}/eventos          → presença em eventos
- GET /deputados/{id}/orgaos           → comissões e órgãos
- GET /deputados/{id}/frentes          → frentes parlamentares
- GET /partidos                        → lista de partidos
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import requests
import streamlit as st
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "CamaraAnalytics/1.0 (projeto educacional)",
}
TIMEOUT = 30


# ── Helper HTTP centralizado ────────────────────────────────────

def _get(
    url: str,
    params: dict | None = None,
    silent: bool = False,
) -> dict | None:
    """
    GET centralizado com tratamento de erros por tipo.

    Args:
        url: URL completa do endpoint.
        params: Parâmetros de query string.
        silent: Se True, suprime warnings na UI (para dados opcionais).

    Returns:
        JSON como dicionário, ou None em caso de falha.
    """
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        if not silent:
            st.warning("⚠️ Sem conexão com a internet.", icon="🌐")
    except requests.exceptions.Timeout:
        if not silent:
            st.warning("⏳ API da Câmara demorou demais para responder.", icon="⏱️")
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response else "?"
        if not silent:
            st.warning(f"⚠️ Erro HTTP {code} na API da Câmara.", icon="🔴")
    except requests.exceptions.RequestException as e:
        if not silent:
            st.warning(f"⚠️ Erro inesperado: {e}", icon="❌")
    return None


def _paginate(
    url: str,
    params: dict,
    silent: bool = False,
    max_paginas: int = 20,
) -> list[dict]:
    """
    Busca paginada genérica usando links HATEOAS (rel='next').

    Args:
        url: URL do endpoint.
        params: Parâmetros base da query.
        silent: Suprimir warnings de erro.
        max_paginas: Limite de segurança contra loops infinitos.

    Returns:
        Lista agregada de todos os registros encontrados.
    """
    todos: list[dict] = []
    p = dict(params)
    p.setdefault("pagina", 1)

    for _ in range(max_paginas):
        data = _get(url, p, silent=silent)
        if not data:
            break
        registros = data.get("dados", [])
        if not registros:
            break
        todos.extend(registros)
        links = data.get("links", [])
        if not any(lnk.get("rel") == "next" for lnk in links):
            break
        p = dict(p)
        p["pagina"] = p.get("pagina", 1) + 1

    return todos


# ── Funções de dados ────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_deputados(
    uf: Optional[str] = None,
    partido: Optional[str] = None,
) -> list[dict]:
    """
    Lista completa de deputados com filtros opcionais. Cache 1h.
    Pagina automaticamente até obter os 513 deputados.
    """
    params: dict = {
        "itens": 100,
        "ordem": "ASC",
        "ordenarPor": "nome",
    }
    if uf:
        params["siglaUf"] = uf
    if partido:
        params["siglaPartido"] = partido

    return _paginate(f"{BASE_URL}/deputados", params)


@st.cache_data(ttl=3600, show_spinner=False)
def get_deputado_detail(deputado_id: int) -> dict:
    """Detalhe completo do deputado (foto, gabinete, email). Cache 1h."""
    data = _get(f"{BASE_URL}/deputados/{deputado_id}")
    return data.get("dados", {}) if data else {}


@st.cache_data(ttl=1800, show_spinner=False)
def get_despesas(deputado_id: int, ano: int) -> pd.DataFrame:
    """
    Todas as despesas CEAP do deputado no ano, com paginação completa. Cache 30min.
    Cada página contém até 100 registros.
    """
    registros = _paginate(
        f"{BASE_URL}/deputados/{deputado_id}/despesas",
        params={"ano": ano, "itens": 100},
        silent=True,
    )
    return pd.DataFrame(registros) if registros else pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner=False)
def get_discursos(deputado_id: int, ano: int) -> pd.DataFrame:
    """
    Discursos do deputado no ano. Cache 30min.

    Campos retornados: dataHoraInicio, tipoDiscurso, urlTexto, faseEvento, etc.
    """
    registros = _paginate(
        f"{BASE_URL}/deputados/{deputado_id}/discursos",
        params={
            "dataInicio": f"{ano}-01-01",
            "dataFim": f"{ano}-12-31",
            "itens": 100,
        },
        silent=True,
    )
    return pd.DataFrame(registros) if registros else pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner=False)
def get_eventos(deputado_id: int, ano: int) -> pd.DataFrame:
    """
    Eventos com participação do deputado no ano. Cache 30min.

    Campos retornados: id, dataHoraInicio, situacao, descricaoTipo, descricao, orgaos.
    """
    registros = _paginate(
        f"{BASE_URL}/deputados/{deputado_id}/eventos",
        params={
            "dataInicio": f"{ano}-01-01",
            "dataFim": f"{ano}-12-31",
            "itens": 100,
        },
        silent=True,
    )
    return pd.DataFrame(registros) if registros else pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_orgaos(deputado_id: int) -> list[dict]:
    """
    Órgãos (comissões) dos quais o deputado é membro. Cache 1h.

    Campos retornados: siglaOrgao, nomeOrgao, titulo, dataInicio, dataFim.
    """
    return _paginate(
        f"{BASE_URL}/deputados/{deputado_id}/orgaos",
        params={"itens": 100},
        silent=True,
    )


@st.cache_data(ttl=3600, show_spinner=False)
def get_frentes_deputado(deputado_id: int) -> list[dict]:
    """
    Frentes parlamentares das quais o deputado é membro. Cache 1h.

    Campos retornados: id, titulo, idLegislatura.
    Nota: a API não aceita `itens` para este endpoint.
    """
    data = _get(f"{BASE_URL}/deputados/{deputado_id}/frentes", silent=True)
    return data.get("dados", []) if data else []


@st.cache_data(ttl=86400, show_spinner=False)
def get_partidos() -> list[str]:
    """Lista ordenada de siglas de partidos com representação na Câmara. Cache 24h."""
    registros = _paginate(f"{BASE_URL}/partidos", params={"itens": 100})
    return sorted([p["sigla"] for p in registros if p.get("sigla")])


@st.cache_data(ttl=86400, show_spinner=False)
def get_ufs() -> list[str]:
    """Lista estática de UFs. Cache 24h."""
    return [
        "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
        "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
        "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
    ]


# ── Helpers de cálculo ──────────────────────────────────────────

def calcular_total_despesas(df: pd.DataFrame) -> float:
    """Soma do valorLiquido de um DataFrame de despesas."""
    if df.empty or "valorLiquido" not in df.columns:
        return 0.0
    return pd.to_numeric(df["valorLiquido"], errors="coerce").fillna(0.0).sum()


@st.cache_data(ttl=86400, show_spinner="Construindo Ranking Global (isso pode levar 1-2 minutos)...")
def get_ranking_gastos_global(ano: int) -> pd.DataFrame:
    """
    Busca o total gasto por CADA UM dos 513 deputados no ano especificado.
    Usa paralelismo para acelerar o processo.
    """
    deputados = get_deputados()
    if not deputados:
        return pd.DataFrame()

    results = []

    def fetch_spending(dep):
        # Para o ranking global, pegamos apenas a primeira página de despesas (itens=1)
        # para obter o total se houver campo 'total' na API, ou apenas pegamos tudo
        # Mas a API não retorna o total no meta da paginação de forma simples e confiável em todos os casos.
        # Então faremos uma busca de despesas mas pedindo o mínimo de dados possível
        # ou pegando a soma.
        
        # Estratégia: somar as despesas do deputado
        # Como queremos o ranking, precisamos dos dados.
        # Para otimizar, como esta função é cacheada por 24h, vamos fazer o trabalho pesado.
        df = get_despesas(dep["id"], ano)
        total = calcular_total_despesas(df)
        return {
            "id": dep["id"],
            "nome": dep["nome"],
            "siglaPartido": dep["siglaPartido"],
            "siglaUf": dep["siglaUf"],
            "total_gasto": total,
            "num_notas": len(df)
        }

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(fetch_spending, deputados))

    df_ranking = pd.DataFrame(results).sort_values("total_gasto", ascending=False)
    return df_ranking.reset_index(drop=True)
