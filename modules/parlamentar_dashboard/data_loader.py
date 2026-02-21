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

# Configuração de Sessão Global para Reuso de Conexões
session = requests.Session()
session.headers.update(HEADERS)

def _get(
    url: str,
    params: dict | None = None,
    silent: bool = False,
) -> dict | None:
    """
    GET centralizado com tratamento de erros, retentativas e validação de JSON.
    """
    try:
        r = session.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        
        # Bug Hunt: Validar se o corpo não está vazio antes de .json()
        if not r.text.strip():
            return None
            
        return r.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        if not silent:
            st.error("🔌 Falha de rede: Verifique sua conexão.", icon="🌐")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            if not silent: st.warning("🐢 A API da Câmara limitou as requisições (Rate Limit). Aguarde um instante.", icon="⏳")
        elif not silent:
            st.warning(f"⚠️ Erro na API (HTTP {e.response.status_code})", icon="🔴")
    except Exception as e:
        if not silent:
            st.warning(f"💣 Erro crítico inesperado: {str(e)[:50]}...", icon="⚠️")
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
        
    # Bug Hunt: Avisar se truncamos os dados
    if len(todos) >= max_paginas * p.get("itens", 100) and not silent:
        st.warning(f"⚠️ Os dados podem estar incompletos (limite de {max_paginas} páginas atingido).", icon="🧱")

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
        max_paginas=50, # Aumentado para 5000 registros p/ garantir ano completo
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



@st.cache_data(ttl=3600, show_spinner=False)
def get_proposicoes(deputado_id: int, ano: int) -> list[dict]:
    """
    Busca proposições de autoria do deputado no ano especificado.
    Filtra por idDeputadoAutor e ano.
    """
    params = {
        "idDeputadoAutor": deputado_id,
        "ano": ano,
        "ordem": "ASC",
        "ordenarPor": "id"
    }
    return _paginate(f"{BASE_URL}/proposicoes", params, silent=True)


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
    """Soma do valorLiquido de um DataFrame de despesas com tratamento de tipos."""
    if df.empty or "valorLiquido" not in df.columns:
        return 0.0
    
    # Bug Hunt: Garantir que valores vazios ou strings de erro não quebrem a soma
    series = pd.to_numeric(df["valorLiquido"], errors="coerce")
    if series.isna().all():
        return 0.0
    return float(series.sum())


@st.cache_data(ttl=86400, show_spinner="Construindo Ranking de Eficiência Global (isso pode levar 2-3 minutos)...")
def get_ranking_gastos_global(ano: int) -> pd.DataFrame:
    """
    Busca o total gasto e a produção legislativa por CADA UM dos 513 deputados.
    Usa cache persistente em disco (24h) para evitar 1026 chamadas de API a cada reload.
    """
    import os
    from pathlib import Path
    from datetime import datetime, timedelta

    # ── Cache em disco ────────────────────────────────────────────────
    CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "cache"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"ranking_global_{ano}.parquet"
    TTL_HORAS = 24

    if cache_file.exists():
        age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if age < timedelta(hours=TTL_HORAS):
            try:
                return pd.read_parquet(cache_file)
            except Exception:
                pass  # cache corrompido — recalcula

    # ── Busca ao vivo ─────────────────────────────────────────────────
    deputados = get_deputados()
    if not deputados:
        return pd.DataFrame()

    results = []

    def fetch_data(dep):
        try:
            df_desp = get_despesas(dep["id"], ano)
            total_gasto = calcular_total_despesas(df_desp)
            proposicoes = get_proposicoes(dep["id"], ano)
            qtd_prop = len(proposicoes)
            custo_por_prop = total_gasto / qtd_prop if qtd_prop > 0 else float('inf')
            return {
                "id":                  dep["id"],
                "nome":                dep["nome"],
                "siglaPartido":        dep["siglaPartido"],
                "siglaUf":             dep["siglaUf"],
                "total_gasto":         total_gasto,
                "num_notas":           len(df_desp),
                "qtd_proposicoes":     qtd_prop,
                "custo_por_proposicao": custo_por_prop,
            }
        except Exception:
            # Não deixa um deputado com erro travar o ranking inteiro
            return None

    with ThreadPoolExecutor(max_workers=20) as executor:
        raw = list(executor.map(fetch_data, deputados))

    results = [r for r in raw if r is not None]
    if not results:
        return pd.DataFrame()

    df_ranking = pd.DataFrame(results).sort_values("total_gasto", ascending=False)
    df_ranking = df_ranking.reset_index(drop=True)

    # Salva cache
    try:
        df_ranking.to_parquet(cache_file, index=False)
    except Exception:
        pass

    return df_ranking
