"""
Ponto de entrada do módulo tracker_gastos.
Uso: python -m modules.tracker_gastos.main --id <ID_DEPUTADO> [--ano ANO] [--mes MES]
"""

import argparse
import sys

from .extractor import get_all_expenses
from .processor import clean_expenses, aggregate_monthly, aggregate_by_supplier
from .reporter import export_csv, export_parquet, print_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extrai e consolida despesas CEAP de um deputado federal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python -m modules.tracker_gastos.main --id 204554
  python -m modules.tracker_gastos.main --id 204554 --ano 2023
  python -m modules.tracker_gastos.main --id 204554 --ano 2023 --mes 6
        """,
    )
    parser.add_argument("--id", type=int, required=True, help="ID do deputado na API da Câmara")
    parser.add_argument("--ano", type=int, default=None, help="Filtrar por ano (ex: 2023)")
    parser.add_argument("--mes", type=int, default=None, help="Filtrar por mês (1-12)")
    parser.add_argument(
        "--formato",
        choices=["csv", "parquet", "ambos"],
        default="ambos",
        help="Formato de exportação (padrão: ambos)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    deputado_id = args.id

    print(f"\n🏛️  Tracker de Gastos — Câmara dos Deputados")
    print(f"{'─'*45}")

    # 1. Extração com paginação
    dados_brutos = get_all_expenses(deputado_id, ano=args.ano, mes=args.mes)

    if not dados_brutos:
        print(f"[AVISO] Nenhuma despesa encontrada para o deputado {deputado_id}.")
        sys.exit(0)

    # 2. Limpeza e processamento
    df_limpo = clean_expenses(dados_brutos)
    df_mensal = aggregate_monthly(df_limpo)
    df_fornecedores = aggregate_by_supplier(df_limpo, top_n=20)

    # 3. Relatório no terminal
    print_summary(df_mensal, titulo=f"Resumo Mensal — Deputado ID {deputado_id}")

    # 4. Exportação
    prefixo = f"deputado_{deputado_id}"
    if args.ano:
        prefixo += f"_{args.ano}"

    if args.formato in ("csv", "ambos"):
        export_csv(df_limpo, f"{prefixo}_despesas_raw")
        export_csv(df_mensal, f"{prefixo}_mensal_categoria")
        export_csv(df_fornecedores, f"{prefixo}_top_fornecedores")

    if args.formato in ("parquet", "ambos"):
        export_parquet(df_limpo, f"{prefixo}_despesas_raw")
        export_parquet(df_mensal, f"{prefixo}_mensal_categoria")

    print("✅ Processamento concluído!")


if __name__ == "__main__":
    main()
