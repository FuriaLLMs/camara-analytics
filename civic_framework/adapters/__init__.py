"""civic_framework/adapters/__init__.py"""
from .base import MunicipalDataSource
from .florianopolis import FlorianopolisAdapter

__all__ = ["MunicipalDataSource", "FlorianopolisAdapter"]
