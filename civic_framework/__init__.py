"""
civic_framework/__init__.py

Framework de Transparência Cívica Municipal — camara-analytics

Uso rápido:
    from civic_framework.adapters import FlorianopolisAdapter
    from civic_framework.collector import DataCollector
    from civic_framework.database import init_db, upsert_vereadores
    from civic_framework.metrics import calcular_ial

    adapter = FlorianopolisAdapter()
    collector = DataCollector(adapter)
    resultado = collector.collect_all()
"""

__version__ = "1.0.0"
__author__ = "camara-analytics"
