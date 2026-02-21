"""
civic_framework/database.py

Banco histórico SQLite para armazenamento normalizado dos dados municipais.

Design:
- Uma tabela por entidade: vereadores, proposicoes, pautas, coletas
- Upsert inteligente: não duplica em recoletas diárias
- Schema versionado: coluna `cidade_id` permite multi-cidade no mesmo banco
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Any, Iterator

log = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "civic_transparency.db"


SCHEMA_SQL = """
-- Metadados das coletas automáticas
CREATE TABLE IF NOT EXISTS coletas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    cidade_id    TEXT NOT NULL,
    recurso      TEXT NOT NULL,
    coletado_em  TEXT NOT NULL,  -- ISO 8601
    total_itens  INTEGER,
    status       TEXT DEFAULT 'ok'
);

-- Vereadores em exercício
CREATE TABLE IF NOT EXISTS vereadores (
    uid          TEXT PRIMARY KEY,  -- <cidade>_<id_original>
    cidade_id    TEXT NOT NULL,
    nome         TEXT,
    partido      TEXT,
    legislatura  TEXT,
    email        TEXT,
    foto_url     TEXT,
    raw_json     TEXT,  -- JSON original preservado para auditoria
    coletado_em  TEXT,
    atualizado_em TEXT
);

-- Proposições legislativas
CREATE TABLE IF NOT EXISTS proposicoes (
    uid          TEXT PRIMARY KEY,
    cidade_id    TEXT NOT NULL,
    tipo         TEXT,
    numero       TEXT,
    ano          INTEGER,
    ementa       TEXT,
    autor        TEXT,
    data_apre    TEXT,  -- data de apresentação (ISO)
    bairro       TEXT,
    status       TEXT,
    raw_json     TEXT,
    coletado_em  TEXT
);

-- Pautas das sessões
CREATE TABLE IF NOT EXISTS pautas (
    uid          TEXT PRIMARY KEY,
    cidade_id    TEXT NOT NULL,
    data_sessao  TEXT,  -- ISO 8601
    tipo_sessao  TEXT,
    titulo       TEXT,
    descricao    TEXT,
    raw_json     TEXT,
    coletado_em  TEXT
);

-- Índices para performance em análises temporais
CREATE INDEX IF NOT EXISTS idx_prop_cidade_ano ON proposicoes (cidade_id, ano);
CREATE INDEX IF NOT EXISTS idx_pautas_data ON pautas (cidade_id, data_sessao);
CREATE INDEX IF NOT EXISTS idx_coletas_cidade ON coletas (cidade_id, recurso);
"""


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    """Context manager para conexão SQLite com commit automático."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")  # performance em leituras concorrentes
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db() -> None:
    """Cria o schema se ainda não existir."""
    with _conn() as con:
        con.executescript(SCHEMA_SQL)
    log.info(f"Banco inicializado: {DB_PATH}")


def registrar_coleta(cidade_id: str, recurso: str, coletado_em: str, total: int, status: str = "ok") -> None:
    """Registra metadados de uma coleta no log histórico."""
    with _conn() as con:
        con.execute(
            "INSERT INTO coletas (cidade_id, recurso, coletado_em, total_itens, status) VALUES (?,?,?,?,?)",
            (cidade_id, recurso, coletado_em, total, status)
        )


def upsert_vereadores(cidade_id: str, registros: List[Dict[str, Any]], coletado_em: str) -> int:
    """
    Insere ou atualiza vereadores.
    Usa uid = '<cidade>_<id>' como chave natural para upsert.
    """
    import json as _json
    n = 0
    with _conn() as con:
        for r in registros:
            id_orig = str(r.get("id") or r.get("codigo") or r.get("idVereador") or _json.dumps(r)[:20])
            uid = f"{cidade_id}_{id_orig}"
            con.execute("""
                INSERT INTO vereadores (uid, cidade_id, nome, partido, email, foto_url, raw_json, coletado_em, atualizado_em)
                VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(uid) DO UPDATE SET
                    nome=excluded.nome, partido=excluded.partido,
                    email=excluded.email, foto_url=excluded.foto_url,
                    raw_json=excluded.raw_json, atualizado_em=excluded.coletado_em
            """, (
                uid, cidade_id,
                r.get("nome") or r.get("nomeVereador"),
                r.get("partido") or r.get("siglaPartido"),
                r.get("email"), r.get("foto") or r.get("urlFoto"),
                _json.dumps(r, ensure_ascii=False),
                coletado_em, coletado_em
            ))
            n += 1
    log.info(f"[{cidade_id}] {n} vereadores upserted")
    return n


def upsert_pautas(cidade_id: str, registros: List[Dict[str, Any]], coletado_em: str) -> int:
    """Insere ou atualiza pautas de sessões."""
    import json as _json
    import hashlib
    n = 0
    with _conn() as con:
        for r in registros:
            # Usa hash do conteúdo como uid natural (APIs municipais raramente têm ID único)
            uid_base = f"{cidade_id}_{r.get('data', '')}_{r.get('titulo', '')}_{r.get('tipo', '')}"
            uid = hashlib.md5(uid_base.encode()).hexdigest()
            con.execute("""
                INSERT OR IGNORE INTO pautas (uid, cidade_id, data_sessao, tipo_sessao, titulo, descricao, raw_json, coletado_em)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                uid, cidade_id,
                r.get("data") or r.get("dataSessao"),
                r.get("tipo") or r.get("tipoSessao"),
                r.get("titulo") or r.get("descricaoTipo"),
                r.get("descricao") or r.get("ementa"),
                _json.dumps(r, ensure_ascii=False), coletado_em
            ))
            n += 1
    log.info(f"[{cidade_id}] {n} pautas processadas")
    return n


def query_vereadores(cidade_id: str) -> List[Dict]:
    """Retorna todos os vereadores de uma cidade."""
    with _conn() as con:
        rows = con.execute("SELECT * FROM vereadores WHERE cidade_id=?", (cidade_id,)).fetchall()
    return [dict(r) for r in rows]


def query_historico_coletas(cidade_id: str) -> List[Dict]:
    """Retorna o histórico de coletas para análise de cobertura."""
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM coletas WHERE cidade_id=? ORDER BY coletado_em DESC LIMIT 100",
            (cidade_id,)
        ).fetchall()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    init_db()
    print(f"✅ Banco criado em: {DB_PATH}")
