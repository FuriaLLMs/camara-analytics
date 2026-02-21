"""
civic_framework/adapters/florianopolis.py

Adapter concreto para a Câmara Municipal de Florianópolis (CMF).
Consome a API JSON-Web pública disponibilizada pela CMF.

API: https://www.cmf.sc.gov.br/jsonweb/web-aplicativo.php
Documentação: https://www.cmf.sc.gov.br/dados-abertos
"""

import requests
import logging
from typing import List, Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import MunicipalDataSource

log = logging.getLogger(__name__)

BASE_URL = "https://www.cmf.sc.gov.br/jsonweb/web-aplicativo.php"
TOKEN = "bdox40jgz46d1o@tg0289kinqs19rgpi5xfvu9f7s88mqs-ee292b83687e83ec319"


class FlorianopolisAdapter(MunicipalDataSource):
    """
    Adapter para a Câmara Municipal de Florianópolis (SC).

    Implementa o contrato MunicipalDataSource usando a API JSON-Web da CMF.
    Trata paginação, retry e bloqueios de WAF automaticamente.
    """

    def __init__(self, timeout: int = 15):
        self._timeout = timeout
        self._session = self._build_session()

    @property
    def cidade(self) -> str:
        return "florianopolis"

    @property
    def uf(self) -> str:
        return "SC"

    def _build_session(self) -> requests.Session:
        """Constrói sessão HTTP com retry e headers de browser real."""
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9",
            "Cache-Control": "no-cache",
        })
        return session

    def _get(self, service: str, extra_params: Optional[Dict] = None) -> List[Dict]:
        """Requisição GET base à API da CMF."""
        params = {"keysoft": TOKEN, "call": service}
        if extra_params:
            params.update(extra_params)
        try:
            resp = self._session.get(BASE_URL, params=params, timeout=self._timeout)
            resp.raise_for_status()
            data = resp.json()
            # A CMF retorna lista direta ou dict com chave variável
            if isinstance(data, list):
                return data
            # Tenta extrair a primeira lista encontrada no dict
            for v in data.values():
                if isinstance(v, list):
                    return v
            return []
        except requests.exceptions.ConnectionError as e:
            log.warning(f"[CMF] Falha de conexão ({service}): {e}")
            return []
        except Exception as e:
            log.error(f"[CMF] Erro inesperado ({service}): {e}")
            return []

    # ── Interface obrigatória ──────────────────────────────────────

    def fetch_vereadores(self) -> List[Dict[str, Any]]:
        return self._get("vereadores")

    def fetch_proposicoes(self, pagina: int = 1, tipo: str = None) -> List[Dict[str, Any]]:
        params = {"pagina": pagina}
        if tipo:
            params["tipo"] = tipo
        return self._get("proposicoes", params)

    def fetch_pautas(self, pagina: int = 1) -> List[Dict[str, Any]]:
        return self._get("pautas", {"pagina": pagina})

    def fetch_noticias(self, pagina: int = 1) -> List[Dict[str, Any]]:
        return self._get("noticias", {"pagina": pagina})

    # ── Extras específicos da CMF ──────────────────────────────────

    def fetch_bairros(self) -> List[Dict[str, Any]]:
        """Bairros de Florianópolis reconhecidos pela CMF."""
        return self._get("bairros")

    def fetch_legislacoes(self, pagina: int = 1) -> List[Dict[str, Any]]:
        return self._get("legislacoes", {"pagina": pagina})

    def fetch_tv_camara(self, pagina: int = 1) -> List[Dict[str, Any]]:
        return self._get("tvcamara", {"pagina": pagina})
