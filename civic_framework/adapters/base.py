"""
civic_framework/adapters/base.py

Contrato base (ABC) para todos os adaptadores de câmaras municipais.
Qualquer nova cidade deve implementar esta interface para ser plugável no framework.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class MunicipalDataSource(ABC):
    """
    Interface abstrata para fontes de dados municipais.

    O Adapter Pattern garante que o framework de transparência
    seja agnóstico à tecnologia de cada câmara — JSON, REST, SOAP, etc.
    Para adicionar uma nova cidade: crie uma subclasse, implemente os métodos.
    """

    @property
    @abstractmethod
    def cidade(self) -> str:
        """Identificador único da cidade (ex: 'florianopolis')."""

    @property
    @abstractmethod
    def uf(self) -> str:
        """Sigla do estado (ex: 'SC')."""

    @abstractmethod
    def fetch_vereadores(self) -> List[Dict[str, Any]]:
        """Retorna lista de vereadores em exercício."""

    @abstractmethod
    def fetch_proposicoes(self, pagina: int = 1, tipo: str = None) -> List[Dict[str, Any]]:
        """Retorna proposições legislativas (com suporte a paginação)."""

    @abstractmethod
    def fetch_pautas(self, pagina: int = 1) -> List[Dict[str, Any]]:
        """Retorna pautas das sessões legislativas."""

    @abstractmethod
    def fetch_noticias(self, pagina: int = 1) -> List[Dict[str, Any]]:
        """Retorna notícias publicadas pela câmara."""

    def fetch_all_pages(self, method_name: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Coleta automática de todas as páginas de um endpoint paginado.

        Uso: adapter.fetch_all_pages('fetch_pautas')
        Continua até receber página vazia.
        """
        method = getattr(self, method_name)
        all_data = []
        pagina = 1
        while True:
            page_data = method(pagina=pagina, **kwargs)
            if not page_data:
                break
            all_data.extend(page_data)
            pagina += 1
            if pagina > 50:  # safety cap — evitar loop infinito
                break
        return all_data
