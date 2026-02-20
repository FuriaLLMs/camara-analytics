"""
Camada de persistência do legis_notifier.
Salva e carrega o ID da última proposição vista para evitar notificações duplicadas.
"""

import json
import os

from .config import PERSISTENCE_FILE


def load_last_id() -> int:
    """
    Carrega o ID da última proposição vista.

    Returns:
        ID da última proposição (0 se nenhuma foi vista ainda).
    """
    if not os.path.exists(PERSISTENCE_FILE):
        return 0

    try:
        with open(PERSISTENCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return int(data.get("last_id", 0))
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"[persistence] Erro ao ler {PERSISTENCE_FILE}: {e}. Usando 0.")
        return 0


def save_last_id(last_id: int) -> None:
    """
    Persiste o ID mais recente no arquivo JSON.

    Args:
        last_id: ID da proposição mais recente processada.
    """
    data = {"last_id": last_id}
    try:
        with open(PERSISTENCE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[persistence] last_id={last_id} salvo em {PERSISTENCE_FILE}")
    except IOError as e:
        print(f"[persistence] Erro ao salvar {PERSISTENCE_FILE}: {e}")


def reset_last_id() -> None:
    """Reinicia o ID, forçando reprocessamento de todas as proposições."""
    save_last_id(0)
    print("[persistence] last_id reiniciado para 0.")
