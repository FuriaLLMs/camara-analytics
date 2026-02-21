
import requests
import json
import pandas as pd
import streamlit as st
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configurações da API CMF (Fallback)
BASE_URL_CMF = "https://www.cmf.sc.gov.br/jsonweb/web-aplicativo.php"
TOKEN_CMF = "bdox40jgz46d1o@tg0289kinqs19rgpi5xfvu9f7s88mqs-ee292b83687e83ec319"

class MunicipalLoader:
    """
    Carrega dados da Câmara Municipal de Florianópolis.
    Prioriza arquivos JSON na pasta 'jsnon/' (Offline-First / Hardcore Mode).
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.base_dir = Path(__file__).parent.parent.parent
        self.jsnon_dir = self.base_dir / "jsnon"
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        })

    def _load_local_json(self, prefix: str) -> List[Dict]:
        """Busca e unifica arquivos JSON que começam com o prefixo na pasta jsnon/."""
        all_data = []
        if not self.jsnon_dir.exists():
            return []
            
        # Lista todos os arquivos que batem com o prefixo (ex: pautas_*.json)
        files = list(self.jsnon_dir.glob(f"{prefix}*.json"))
        
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        all_data.extend(content)
                    elif isinstance(content, dict):
                        # Algumas APIs retornam {"dados": [...]}
                        all_data.extend(content.get("dados", []))
            except Exception as e:
                print(f"Erro ao ler arquivo local {file_path}: {e}")
                
        # Deduplicação básica por link ou título (evita overlaps de abas)
        seen = set()
        unique_data = []
        for item in all_data:
            key = item.get("link") or item.get("url") or item.get("id") or item.get("titulo")
            if key not in seen:
                unique_data.append(item)
                seen.add(key)
        
        return unique_data

    def _fetch(self, service: str, params: Optional[Dict] = None) -> List[Dict]:
        """Fetch híbrido: tenta local primeiro, senão vai na API."""
        # Tenta carregar localmente primeiro (Offline-First)
        local = self._load_local_json(service)
        if local:
            return local

        # Fallback para API (caso o arquivo local não exista ou esteja vazio)
        url_params = {"keysoft": TOKEN_CMF, "call": service}
        if params: url_params.update(params)
            
        try:
            response = self.session.get(BASE_URL_CMF, params=url_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else data.get("dados", [])
        except Exception:
            return []

    @st.cache_data(ttl=3600)
    def get_vereadores(_self) -> List[Dict]:
        """Lista vereadores (Prioriza local jsnon/vereadores_*.json)."""
        return _self._fetch("vereadores")

    @st.cache_data(ttl=3600)
    def get_pautas(_self) -> List[Dict]:
        """Retorna TODAS as pautas unificadas dos arquivos locais."""
        # Forçamos a busca local massiva
        return _self._load_local_json("pautas")

    @st.cache_data(ttl=3600)
    def get_noticias(_self) -> List[Dict]:
        """Retorna TODAS as notícias unificadas dos arquivos locais."""
        return _self._load_local_json("noticias")

    @st.cache_data(ttl=3600)
    def get_tipos_proposicoes(_self) -> List[Dict]:
        return _self._fetch("proposicoes")

    @st.cache_data(ttl=3600)
    def get_bairros(_self) -> List[Dict]:
        return _self._fetch("bairros")

    @st.cache_data(ttl=3600)
    def get_atendimento(_self) -> List[Dict]:
        return _self._fetch("atendimento")

    @st.cache_data(ttl=3600)
    def get_tv_camara(_self) -> List[Dict]:
        return _self._fetch("tvcamara")

    def get_proposicoes_lista(_self, max_paginas: int = 5) -> List[Dict]:
        """Mantido para compatibilidade, mas prioriza o fluxo offline."""
        return _self._fetch("proposicoes") # Simplificado para o modo hardcore

