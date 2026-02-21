"""
civic_framework/collector.py

DataCollector: responsável pela coleta automática e armazenamento
de dados brutos com versionamento histórico por data.

Design:
- Um arquivo JSON por recurso por dia: data/raw/<cidade>/<recurso>/<YYYYMMDD>.json
- Metadata de coleta é salva junto (timestamp, status, quantidade)
- Coleta idempotente: rodar 2x no mesmo dia sobrescreve, não duplica
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from civic_framework.adapters.base import MunicipalDataSource

log = logging.getLogger(__name__)

# Raiz dos dados brutos — relativa à raiz do projeto
RAW_DATA_ROOT = Path(__file__).parent.parent / "data" / "raw"


class DataCollector:
    """
    Coleta dados via adapter e os persiste em JSON versionado por data.

    Uso:
        adapter = FlorianopolisAdapter()
        collector = DataCollector(adapter)
        resultado = collector.collect_all()
    """

    # Recursos a coletar: (nome_arquivo, método, é_paginado)
    RESOURCES = [
        ("vereadores",   "fetch_vereadores",  False),
        ("pautas",       "fetch_pautas",      True),
        ("noticias",     "fetch_noticias",    True),
        ("proposicoes",  "fetch_proposicoes", True),
    ]

    def __init__(self, adapter: MunicipalDataSource):
        self.adapter = adapter
        self.base_path = RAW_DATA_ROOT / adapter.cidade
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _today(self) -> str:
        return datetime.now(tz=timezone.utc).strftime("%Y%m%d")

    def _collect_resource(self, recurso: str, method_name: str, paginado: bool) -> Dict[str, Any]:
        """Coleta um recurso e retorna metadata + dados."""
        log.info(f"[{self.adapter.cidade}] Coletando: {recurso}...")
        inicio = datetime.now(tz=timezone.utc)

        if paginado:
            dados = self.adapter.fetch_all_pages(method_name)
        else:
            method = getattr(self.adapter, method_name)
            dados = method()

        duracao_ms = int((datetime.now(tz=timezone.utc) - inicio).total_seconds() * 1000)

        return {
            "_meta": {
                "recurso": recurso,
                "cidade": self.adapter.cidade,
                "uf": self.adapter.uf,
                "coletado_em": inicio.isoformat(),
                "duracao_ms": duracao_ms,
                "total_registros": len(dados),
                "versao_schema": "1.0",
            },
            "dados": dados,
        }

    def collect_all(self, dry_run: bool = False) -> Dict[str, bool]:
        """
        Coleta todos os recursos do adapter.

        dry_run=True → faz a coleta mas não salva em disco.
        Retorna dict {recurso: sucesso}.
        """
        hoje = self._today()
        resultados = {}

        for recurso, method_name, paginado in self.RESOURCES:
            try:
                payload = self._collect_resource(recurso, method_name, paginado)
                n = payload["_meta"]["total_registros"]

                if dry_run:
                    log.info(f"[DRY-RUN] {recurso}: {n} registros (não salvo)")
                    resultados[recurso] = True
                    continue

                # Salva em data/raw/<cidade>/<recurso>/<YYYYMMDD>.json
                destino = self.base_path / recurso
                destino.mkdir(parents=True, exist_ok=True)
                arquivo = destino / f"{hoje}.json"

                with open(arquivo, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)

                log.info(f"[{self.adapter.cidade}] {recurso}: {n} registros → {arquivo}")
                resultados[recurso] = True

            except Exception as e:
                log.error(f"[{self.adapter.cidade}] Falha em '{recurso}': {e}")
                resultados[recurso] = False

        return resultados

    def list_snapshots(self, recurso: str) -> List[str]:
        """Lista todas as datas disponíveis para um recurso (para análise histórica)."""
        path = self.base_path / recurso
        if not path.exists():
            return []
        return sorted([f.stem for f in path.glob("*.json")])

    def load_snapshot(self, recurso: str, data: str = None) -> List[Dict]:
        """
        Carrega snapshot de uma data específica (ou o mais recente).

        data: 'YYYYMMDD' ou None (carrega o mais recente)
        """
        snapshots = self.list_snapshots(recurso)
        if not snapshots:
            return []

        target = data if data in snapshots else snapshots[-1]
        arquivo = self.base_path / recurso / f"{target}.json"

        with open(arquivo, encoding="utf-8") as f:
            payload = json.load(f)

        return payload.get("dados", [])


# ── CLI mínima para execução via cron ──────────────────────────────
if __name__ == "__main__":
    import argparse
    from civic_framework.adapters.florianopolis import FlorianopolisAdapter

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Coleta dados municipais")
    parser.add_argument("--cidade", default="florianopolis", help="Cidade alvo")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem salvar")
    args = parser.parse_args()

    adapters = {"florianopolis": FlorianopolisAdapter}
    AdapterClass = adapters.get(args.cidade)

    if not AdapterClass:
        print(f"Cidade '{args.cidade}' não implementada. Disponíveis: {list(adapters.keys())}")
        exit(1)

    collector = DataCollector(AdapterClass())
    resultado = collector.collect_all(dry_run=args.dry_run)
    print("\n── Resultado da Coleta ──")
    for recurso, ok in resultado.items():
        print(f"  {'✅' if ok else '❌'} {recurso}")
