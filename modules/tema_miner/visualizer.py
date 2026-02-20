"""
Visualizações do módulo tema_miner.
Gera WordCloud e gráfico de frequência de termos legislativos.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import Counter
from wordcloud import WordCloud


# Paleta para o gráfico de barras
COR_BARRAS = "#4A90D9"
COR_DESTAQUE = "#E74C3C"


def generate_wordcloud(
    tokens: list[str],
    titulo: str = "Temas Mais Frequentes — Ementas Legislativas",
    output_path: str = None,
) -> plt.Figure:
    """
    Gera e exibe uma WordCloud a partir de uma lista de tokens.

    Args:
        tokens: Lista de tokens já processados.
        titulo: Título do gráfico.
        output_path: Caminho para salvar a imagem (None = não salvar).

    Returns:
        Figura Matplotlib.
    """
    if not tokens:
        print("[visualizer] Nenhum token disponível para gerar WordCloud.")
        return None

    # Juntar tokens como texto para a WordCloud
    texto = " ".join(tokens)

    wc = WordCloud(
        width=1600,
        height=900,
        background_color="#0f1117",
        colormap="Blues",
        max_words=200,
        min_font_size=10,
        max_font_size=120,
        collocations=False,
        prefer_horizontal=0.7,
    ).generate(texto)

    fig, ax = plt.subplots(figsize=(16, 9), facecolor="#0f1117")
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(titulo, color="white", fontsize=18, pad=20, fontweight="bold")
    plt.tight_layout(pad=0)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        print(f"[visualizer] WordCloud salva → {output_path}")

    print("[visualizer] WordCloud gerada com sucesso.")
    return fig


def plot_frequency_bar(
    counter: Counter,
    top_n: int = 20,
    titulo: str = "Frequência de Termos nas Ementas Legislativas",
    output_path: str = None,
) -> plt.Figure:
    """
    Gráfico de barras horizontal com os termos mais frequentes.

    Args:
        counter: Counter de frequências.
        top_n: Quantidade de termos a exibir.
        titulo: Título do gráfico.
        output_path: Caminho para salvar (None = não salvar).

    Returns:
        Figura Matplotlib.
    """
    if not counter:
        print("[visualizer] Counter vazio, nada a plotar.")
        return None

    top = counter.most_common(top_n)
    termos = [t[0] for t in top][::-1]   # Invertido para barras horizontais (menor→ maior)
    freqs = [t[1] for t in top][::-1]

    # Coloração: top 3 em cor de destaque, demais em azul
    cores = [COR_DESTAQUE if i >= len(termos) - 3 else COR_BARRAS for i in range(len(termos))]

    fig, ax = plt.subplots(figsize=(12, 8), facecolor="#0f1117")
    ax.set_facecolor("#1a1a2e")

    barras = ax.barh(termos, freqs, color=cores, alpha=0.88, edgecolor="none", height=0.65)

    # Valores nas barras
    for barra, freq in zip(barras, freqs):
        ax.text(
            barra.get_width() + max(freqs) * 0.01,
            barra.get_y() + barra.get_height() / 2,
            str(freq),
            va="center",
            color="white",
            fontsize=9,
        )

    ax.set_xlabel("Frequência", color="white", fontsize=11)
    ax.set_title(titulo, color="white", fontsize=14, pad=15, fontweight="bold")
    ax.tick_params(colors="white", labelsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("#444")
    ax.spines["left"].set_color("#444")
    ax.xaxis.label.set_color("white")
    ax.set_xlim(0, max(freqs) * 1.15)

    # Legenda
    legenda = [
        mpatches.Patch(color=COR_DESTAQUE, label="Top 3 termos"),
        mpatches.Patch(color=COR_BARRAS, label="Demais termos"),
    ]
    ax.legend(handles=legenda, facecolor="#2c2c54", labelcolor="white", fontsize=9)

    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        print(f"[visualizer] Gráfico de frequência salvo → {output_path}")

    return fig
