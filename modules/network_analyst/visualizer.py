"""
Visualizador de grafos políticos com Matplotlib.
Plota o grafo de redes deputado ↔ frente com layout spring e coloração por tipo de nó.
"""

import os
import matplotlib
matplotlib.use("Agg")  # Backend não-interativo para salvar imagens
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx


# Paleta de cores
COR_DEPUTADO = "#4A90D9"   # Azul
COR_FRENTE = "#E74C3C"     # Vermelho
COR_PONTE = "#F39C12"      # Laranja (deputados com alta centralidade)


def plot_network(
    G: nx.Graph,
    top_pontes: list[tuple[str, float]] = None,
    titulo: str = "Rede de Influência — Câmara dos Deputados",
    figsize: tuple = (20, 14),
) -> plt.Figure:
    """
    Plota o grafo de redes com spring layout.

    Args:
        G: Grafo NetworkX.
        top_pontes: Lista de (nó, score) de nós-ponte (serão destacados).
        titulo: Título do gráfico.
        figsize: Tamanho da figura (largura, altura) em polegadas.

    Returns:
        Objeto Figure do Matplotlib.
    """
    if G.number_of_nodes() == 0:
        print("[visualizer] Grafo vazio, nada a plotar.")
        return None

    print(f"[visualizer] Calculando layout spring (pode demorar para grafos grandes)...")

    # Calcular layout
    pos = nx.spring_layout(G, seed=42, k=0.8)

    # Determinar cores dos nós
    nos_ponte = {n for n, _ in top_pontes} if top_pontes else set()
    cores_nos = []
    tamanhos_nos = []

    for node in G.nodes():
        tipo = G.nodes[node].get("tipo", "")
        if tipo == "frente":
            cores_nos.append(COR_FRENTE)
            tamanhos_nos.append(200)
        elif node in nos_ponte:
            cores_nos.append(COR_PONTE)
            tamanhos_nos.append(350)
        else:
            cores_nos.append(COR_DEPUTADO)
            tamanhos_nos.append(80)

    fig, ax = plt.subplots(figsize=figsize, facecolor="#1a1a2e")
    ax.set_facecolor("#1a1a2e")

    # Desenhar arestas
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        alpha=0.15,
        edge_color="#AAAAAA",
        width=0.5,
    )

    # Desenhar nós
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=cores_nos,
        node_size=tamanhos_nos,
        alpha=0.85,
    )

    # Labels apenas para frentes (evitar poluição visual)
    frente_labels = {
        n: G.nodes[n].get("titulo", n)[:20] + "..."
        for n in G.nodes()
        if G.nodes[n].get("tipo") == "frente"
    }
    nx.draw_networkx_labels(
        G, pos, labels=frente_labels, ax=ax,
        font_size=5, font_color="white", font_weight="bold",
    )

    # Legenda
    legend_items = [
        mpatches.Patch(color=COR_DEPUTADO, label="Deputado"),
        mpatches.Patch(color=COR_FRENTE, label="Frente Parlamentar"),
        mpatches.Patch(color=COR_PONTE, label="Nó Ponte (alta centralidade)"),
    ]
    ax.legend(handles=legend_items, loc="upper left", fontsize=9,
              facecolor="#2c2c54", labelcolor="white", framealpha=0.8)

    ax.set_title(titulo, color="white", fontsize=14, pad=15, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()

    print("[visualizer] Grafo plotado com sucesso.")
    return fig


def save_graph(fig: plt.Figure, filepath: str, dpi: int = 150) -> None:
    """
    Salva a figura do grafo em arquivo de imagem.

    Args:
        fig: Figura Matplotlib retornada por plot_network().
        filepath: Caminho completo do arquivo de saída (ex: outputs/grafo.png).
        dpi: Resolução da imagem.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fig.savefig(filepath, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[visualizer] Grafo salvo → {filepath}")
