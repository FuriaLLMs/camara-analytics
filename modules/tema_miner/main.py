"""
Ponto de entrada do módulo tema_miner.
Uso: python -m modules.tema_miner.main --ano 2024 [--tipo PL] [--top 20]
"""

import argparse
import os
import sys

from .fetcher import get_ementas
from .cleaner import process_ementas
from .analyzer import count_frequencies, get_top_terms, get_term_stats
from .visualizer import generate_wordcloud, plot_frequency_bar


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mineração de temas em ementas legislativas da Câmara dos Deputados.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python -m modules.tema_miner.main --ano 2024
  python -m modules.tema_miner.main --ano 2023 --tipo PEC --top 30
  python -m modules.tema_miner.main --ano 2024 --paginas 20 --sem-graficos
        """,
    )
    parser.add_argument("--ano", type=int, required=True, help="Ano das proposições a analisar")
    parser.add_argument("--tipo", type=str, default="PL", help="Sigla do tipo de proposição (padrão: PL)")
    parser.add_argument("--top", type=int, default=20, help="Quantidade de termos no ranking (padrão: 20)")
    parser.add_argument("--paginas", type=int, default=10, help="Número de páginas a buscar (padrão: 10)")
    parser.add_argument("--sem-graficos", action="store_true", help="Pular geração de imagens")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print(f"\n🔬 Tema Miner — Câmara dos Deputados")
    print("─" * 45)
    print(f"  Ano: {args.ano} | Tipo: {args.tipo} | Top: {args.top}")

    # 1. Coletar ementas
    ementas = get_ementas(ano=args.ano, tipo_sigla=args.tipo, max_paginas=args.paginas)

    if not ementas:
        print("[AVISO] Nenhuma ementa coletada. Verifique os parâmetros.")
        sys.exit(0)

    # 2. Processar (limpar + tokenizar)
    print("\n🧹 Processando texto...")
    tokens = process_ementas(ementas)

    if not tokens:
        print("[AVISO] Nenhum token gerado após processamento.")
        sys.exit(0)

    # 3. Análise de frequência
    print("\n📊 Analisando frequências...")
    counter = count_frequencies(tokens)
    top_termos = get_top_terms(counter, n=args.top)
    stats = get_term_stats(counter)

    print(f"\n📈 Estatísticas gerais:")
    print(f"  • Total de tokens:      {stats.get('total_tokens', 0):,}")
    print(f"  • Termos únicos:        {stats.get('termos_unicos', 0):,}")
    print(f"  • Frequência média:     {stats.get('media_frequencia', 0):.1f}")
    if stats.get("termo_mais_frequente"):
        termo, freq = stats["termo_mais_frequente"]
        print(f"  • Termo mais frequente: '{termo}' ({freq} ocorrências)")

    # 4. Visualizações
    output_dir = "outputs/tema_miner"
    os.makedirs(output_dir, exist_ok=True)

    if not args.sem_graficos:
        print("\n🎨 Gerando WordCloud...")
        fig_wc = generate_wordcloud(
            tokens,
            titulo=f"Temas em Ementas de {args.tipo} — {args.ano}",
            output_path=os.path.join(output_dir, f"wordcloud_{args.tipo}_{args.ano}.png"),
        )

        print("📊 Gerando gráfico de frequência...")
        fig_bar = plot_frequency_bar(
            counter,
            top_n=args.top,
            titulo=f"Top {args.top} Termos — {args.tipo} {args.ano}",
            output_path=os.path.join(output_dir, f"frequencia_{args.tipo}_{args.ano}.png"),
        )

    # 5. Salvar CSV de frequências
    import csv
    csv_path = os.path.join(output_dir, f"termos_{args.tipo}_{args.ano}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["termo", "frequencia"])
        writer.writerows(counter.most_common())
    print(f"\n💾 CSV de frequências salvo → {csv_path}")
    print(f"💾 Imagens salvas em → {output_dir}/")

    print("\n✅ Mineração de temas concluída!")


if __name__ == "__main__":
    main()
