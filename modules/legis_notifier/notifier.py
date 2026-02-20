"""
Notificador via Telegram Bot API.
Envia mensagens formatadas sobre novas proposições legislativas.
"""

import requests

from .config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def send_telegram(message: str, parse_mode: str = "Markdown") -> bool:
    """
    Envia uma mensagem para o chat do Telegram configurado.

    Args:
        message: Texto da mensagem (suporta Markdown).
        parse_mode: Modo de formatação ('Markdown' ou 'HTML').

    Returns:
        True se enviado com sucesso, False caso contrário.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[notifier] ⚠️  TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID não configurado no .env!")
        print(f"[notifier] Mensagem que seria enviada:\n{message}")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"[notifier] ✅ Mensagem enviada ao Telegram (chat: {TELEGRAM_CHAT_ID})")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"[notifier] ❌ Erro HTTP ao enviar Telegram: {e}")
        print(f"[notifier] Resposta: {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[notifier] ❌ Erro de conexão ao enviar Telegram: {e}")
        return False


def send_batch(messages: list[str]) -> int:
    """
    Envia múltiplas mensagens em sequência.

    Args:
        messages: Lista de mensagens a enviar.

    Returns:
        Número de mensagens enviadas com sucesso.
    """
    enviadas = 0
    for msg in messages:
        if send_telegram(msg):
            enviadas += 1
    return enviadas
