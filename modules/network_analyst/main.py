"""
Ponto de entrada do módulo network_analyst.
Uso: python -m modules.network_analyst.main [--legislatura NUM] [--top-pontes N]
"""

import argparse
import json
import os

from .fetcher import get_frentes, get_deputados, build_frente_deputado_map
from .graph_builder import build_graph, get_bridge_nodes, get_degree_stats
from .visualizer import plot_network, save_graph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisa redes de influência entre deputados e frentes parlamentares."
    )
    parser.add_argument("--legislatura", type=int, default=None, help="Número da legislatura (ex: 57)")
    parser.add_argument("--top-pontes", type=int, default=15, help="Quantidade de nós-ponte a destacar")
    parser.add_argument("--sem-grafo", action="store_true", help="Pular a geração do gráfico (mais rápido)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("\n🕸️  Network Analyst — Câmara dos Deputados")
    print("─" * 45)

    # 1. Coletar dados
    print("\n📡 Coletando frentes parlamentares...")
    frentes = get_frentes(args.legislatura)

    if not frentes:
        print("[AVISO] Nenhuma frente encontrada. Verifique a conexão ou o número da legislatura.")
        return

    print(f"\n📡 Coletando membros de {len(frentes)} frentes (pode demorar)...")
    frente_membro_map = build_frente_deputado_map(frentes, delay=0.4)

    # 2. Construir grafo
    print("\n🔗 Construindo grafo de redes...")
    G = build_graph(frente_membro_map, frentes)

    # 3. Estatísticas
    stats = get_degree_stats(G)
    print(f"\n📊 Estatísticas do Grafo:")
    print(f"  • Nós totais:          {stats['total_nos']}")
    print(f"  • Arestas totais:      {stats['total_arestas']}")
    print(f"  • Deputados no grafo:  {stats['total_deputados']}")
    print(f"  • Frentes no grafo:    {stats['total_frentes']}")
    print(f"  • Máx. frentes/dep.:   {stats['max_frentes_por_dep']}")
    print(f"  • Média frentes/dep.:  {stats['media_frentes_por_dep']:.2f}")

    # 4. Identificar pontes
    top_pontes = get_bridge_nodes(G, top_n=args.top_pontes)
    print(f"\n🌉 Top {args.top_pontes} Deputados-Ponte (maior centralidade de intermediação):")
    for i, (node, score) in enumerate(top_pontes[:10], 1):
        nome = G.nodes[node].get("nome", node)
        partido = G.nodes[node].get("partido", "?")
        uf = G.nodes[node].get("uf", "?")
        print(f"  {i:2}. {nome} ({partido}/{uf}) — score: {score:.4f}")

    # 5. Salvar dados JSON
    output_dir = "outputs/network_analyst"
    os.makedirs(output_dir, exist_ok=True)

    pontes_data = [
        {
            "no": node,
            "score": score,
            "nome": G.nodes[node].get("nome"),
            "partido": G.nodes[node].get("partido"),
            "uf": G.nodes[node].get("uf"),
        }
        for node, score in top_pontes
    ]

    with open(os.path.join(output_dir, "pontes.json"), "w", encoding="utf-8") as f:
        json.dump(pontes_data, f, ensure_ascii=False, indent=2)

    with open(os.path.join(output_dir, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Dados salvos em: {output_dir}/")

    # 6. Visualizar grafo
    if not args.sem_grafo:
        print("\n🎨 Gerando visualização do grafo...")
        fig = plot_network(G, top_pontes=top_pontes)
        if fig:
            save_graph(fig, os.path.join(output_dir, "grafo_rede_politica.png"))

    print("\n✅ Análise de redes concluída!")


if __name__ == "__main__":
    main()
