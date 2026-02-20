"""
Ponto de entrada do módulo legis_notifier.
Monitora proposições legislativas em loop e envia alertas via Telegram.
Uso: python -m modules.legis_notifier.main [--uma-vez] [--reset]
"""

import argparse
import time
import sys

from .config import PALAVRAS_CHAVE, INTERVALO_SEGUNDOS
from .monitor import check_new_proposicoes, format_proposicao_message
from .notifier import send_batch
from .persistence import save_last_id, reset_last_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitora proposições legislativas e envia alertas via Telegram."
    )
    parser.add_argument(
        "--uma-vez",
        action="store_true",
        help="Executar apenas uma verificação (não loop contínuo)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reiniciar o last_id (reprocessar tudo)",
    )
    parser.add_argument(
        "--palavras",
        type=str,
        default=None,
        help="Palavras-chave separadas por vírgula (ex: 'educação,saúde')",
    )
    return parser.parse_args()


def run_check(palavras: list[str]) -> None:
    """Executa uma rodada de verificação e envio de notificações."""
    print(f"\n🔍 Verificando proposições... (palavras: {', '.join(palavras)})")
    novas = check_new_proposicoes(palavras)

    if not novas:
        print("  → Nenhuma novidade encontrada.")
        return

    # Formatar e enviar mensagens
    mensagens = [format_proposicao_message(p) for p in novas]
    enviadas = send_batch(mensagens)
    print(f"  → {enviadas}/{len(mensagens)} notificações enviadas.")

    # Atualizar last_id com o ID mais alto encontrado
    max_id = max(p.get("id", 0) for p in novas)
    save_last_id(max_id)


def main() -> None:
    args = parse_args()

    print("\n📢 Legis Notifier — Câmara dos Deputados")
    print("─" * 45)

    if args.reset:
        reset_last_id()

    palavras = [p.strip() for p in args.palavras.split(",")] if args.palavras else PALAVRAS_CHAVE
    print(f"🔎 Monitorando: {', '.join(palavras)}")

    if args.uma_vez:
        run_check(palavras)
        print("\n✅ Verificação única concluída.")
        sys.exit(0)

    # Loop contínuo
    print(f"⏱️  Intervalo de verificação: {INTERVALO_SEGUNDOS // 60} minutos")
    print("   Pressione Ctrl+C para parar.\n")

    try:
        while True:
            run_check(palavras)
            print(f"\n💤 Aguardando {INTERVALO_SEGUNDOS // 60} min até próxima verificação...")
            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor encerrado pelo usuário.")
        sys.exit(0)


if __name__ == "__main__":
    main()
