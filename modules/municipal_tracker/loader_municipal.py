"""
Conector de Dados para a Câmara Municipal de Florianópolis (CMF).
Implementa o consumo da API JSON-Web para o projeto Transparência Vertical (V5.0).
"""

import requests
import pandas as pd
import streamlit as st
from typing import List, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configurações da API CMF
BASE_URL_CMF = "https://www.cmf.sc.gov.br/jsonweb/web-aplicativo.php"
TOKEN_CMF = "bdox40jgz46d1o@tg0289kinqs19rgpi5xfvu9f7s88mqs-ee292b83687e83ec319"

class MunicipalLoader:
    """Carrega dados da Câmara Municipal de Florianópolis."""
    
    def __init__(self):
        self.session = requests.Session()
        # Estratégia de Retry para lidar com 'Connection Reset'
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Headers completos para mimetizar um navegador real (evita bloqueios de WAF)
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Connection": "keep-alive"
        })

    def _fetch(self, service: str, params: Optional[Dict] = None) -> List[Dict]:
        """Método base para requisições GET à CMF."""
        url_params = {
            "keysoft": TOKEN_CMF,
            "call": service
        }
        if params:
            url_params.update(params)
            
        try:
            response = self.session.get(BASE_URL_CMF, params=url_params, timeout=15)
            response.raise_for_status()
            data = response.json()
            # A API da CMF costuma retornar uma lista direta ou um dicionário com os dados
            return data if isinstance(data, list) else data.get("dados", [])
        except Exception as e:
            st.error(f"Erro ao acessar CMF ({service}): {e}")
            return []

    @st.cache_data(ttl=3600)
    def get_vereadores(_self) -> List[Dict]:
        """Lista vereadores em exercício em Florianópolis."""
        return _self._fetch("vereadores")

    @st.cache_data(ttl=1800)
    def get_pautas(_self, pagina: int = 1) -> List[Dict]:
        """Lista as pautas das sessões da CMF."""
        return _self._fetch("pautas", {"pagina": pagina})

    @st.cache_data(ttl=1800)
    def get_noticias(_self, pagina: int = 1) -> List[Dict]:
        """Lista as notícias da Câmara Municipal."""
        return _self._fetch("noticias", {"pagina": pagina})

    @st.cache_data(ttl=3600)
    def get_tipos_proposicoes(_self) -> List[Dict]:
        """Lista os tipos de proposições legislativas municipais."""
        return _self._fetch("proposicoes")

    @st.cache_data(ttl=3600)
    def get_bairros(_self) -> List[Dict]:
        """Lista os bairros de Florianópolis atendidos."""
        return _self._fetch("bairros")

    @st.cache_data(ttl=1800)
    def get_tv_camara(_self, pagina: int = 1) -> List[Dict]:
        """Lista vídeos da TV Câmara de Florianópolis."""
        return _self._fetch("tvcamara", {"pagina": pagina})

    @st.cache_data(ttl=3600)
    def get_proposicoes_lista(_self, max_paginas: int = 5) -> List[Dict]:
        """
        Busca proposicões reais varrendo as páginas disponíveis.
        Primeiro lista os tipos, depois busca proposições de cada tipo.
        """
        tipos = _self._fetch("proposicoes")
        todas = []
        # Tenta pelos primeiros tipos disponibilizados pela API
        for tipo in tipos[:3]:  # limita pra não demorar demais
            contract = tipo.get("contract") or tipo.get("id") or tipo.get("codigo")
            if not contract:
                continue
            for pagina in range(1, max_paginas + 1):
                dados = _self._fetch("proposicoes", {"tipo": contract, "pagina": pagina})
                if not dados:
                    break
                todas.extend(dados)
        return todas

    @st.cache_data(ttl=1800)
    def get_noticias_todas(_self, max_paginas: int = 5) -> List[Dict]:
        """Busca notícias varrendo múltiplas páginas para ampliar o pool de busca."""
        todas = []
        for pagina in range(1, max_paginas + 1):
            dados = _self._fetch("noticias", {"pagina": pagina})
            if not dados:
                break
            todas.extend(dados)
        return todas
