"""
Monitor de proposições legislativas.
Consulta o endpoint /proposicoes filtrando por palavras-chave e detecta novidades.
"""

import requests
from typing import Optional

from .config import BASE_URL, HEADERS, REQUEST_TIMEOUT
from .persistence import load_last_id


def check_new_proposicoes(
    keywords: list[str],
    tipo_sigla: Optional[str] = "PL",
    max_results: int = 20,
) -> list[dict]:
    """
    Consulta proposições recentes e retorna apenas as novas (id > last_id).

    Args:
        keywords: Lista de palavras-chave para filtrar ementas.
        tipo_sigla: Sigla do tipo de proposição (ex: 'PL', 'PEC', 'MP').
        max_results: Número máximo de proposições a buscar por keyword.

    Returns:
        Lista de proposições novas (não vistas anteriormente).
    """
    last_id = load_last_id()
    novas: list[dict] = []
    ids_vistos: set[int] = set()

    for keyword in keywords:
        url = f"{BASE_URL}/proposicoes"
        params = {
            "keywords": keyword,
            "itens": max_results,
            "ordem": "DESC",
            "ordenarPor": "id",
        }
        if tipo_sigla:
            params["siglaTipo"] = tipo_sigla

        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            proposicoes = response.json().get("dados", [])
        except requests.exceptions.RequestException as e:
            print(f"[monitor] Erro ao buscar keyword '{keyword}': {e}")
            continue

        for prop in proposicoes:
            pid = prop.get("id")
            if pid and pid > last_id and pid not in ids_vistos:
                ids_vistos.add(pid)
                prop["_keyword"] = keyword  # Marcar qual keyword ativou
                novas.append(prop)

    # Ordenar do mais recente para o mais antigo
    novas.sort(key=lambda x: x.get("id", 0), reverse=True)
    print(f"[monitor] {len(novas)} proposição(ões) nova(s) encontrada(s).")
    return novas


def format_proposicao_message(prop: dict) -> str:
    """
    Formata uma proposição como mensagem de texto para enviar via Telegram.

    Args:
        prop: Dicionário de proposição retornado pela API.

    Returns:
        Mensagem formatada em texto.
    """
    pid = prop.get("id", "N/A")
    sigla = prop.get("siglaTipo", "")
    numero = prop.get("numero", "")
    ano = prop.get("ano", "")
    ementa = prop.get("ementa", "Sem descrição.")
    keyword = prop.get("_keyword", "")
    uri = prop.get("uri", "")

    msg = (
        f"🏛️ *Nova Proposição Detectada*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📄 *{sigla} {numero}/{ano}*\n"
        f"🔍 Palavra-chave: `{keyword}`\n\n"
        f"📝 *Ementa:*\n{ementa[:400]}{'...' if len(ementa) > 400 else ''}\n\n"
        f"🔗 [Ver na Câmara]({uri})\n"
        f"ID: `{pid}`"
    )
    return msg
