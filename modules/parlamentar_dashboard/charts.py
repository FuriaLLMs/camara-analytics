"""
Gráficos Plotly para o dashboard parlamentar — design premium para cliente final.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Paleta de cores curada ──────────────────────────────────────
CORES_CATEGORIAS = [
    "#4A90D9", "#E8654A", "#50C878", "#FFB347", "#9B59B6",
    "#1ABC9C", "#E74C3C", "#3498DB", "#F39C12", "#2ECC71",
    "#E91E63", "#00BCD4", "#FF5722", "#8BC34A", "#673AB7",
]

BG_CARD   = "#111827"   # Fundo dos cards
BG_PLOT   = "#1F2937"   # Fundo dos gráficos
BORDA     = "#374151"   # Bordas
TEXTO     = "#F9FAFB"   # Texto principal
TEXTO2    = "#9CA3AF"   # Texto secundário
AZUL      = "#3B82F6"   # Azul destaque
VERDE     = "#10B981"   # Verde sucesso
AMARELO   = "#F59E0B"   # Amarelo atenção
VERMELHO  = "#EF4444"   # Vermelho alert

_FONTE = dict(family="Inter, 'Segoe UI', sans-serif")


def _layout(**extra) -> dict:
    """Base de layout dark premium."""
    base = dict(
        paper_bgcolor=BG_CARD,
        plot_bgcolor=BG_PLOT,
        font=dict(color=TEXTO, family=_FONTE["family"], size=13),
        title_font=dict(color=TEXTO, size=17, family=_FONTE["family"]),
        margin=dict(t=60, l=20, r=20, b=30),
        coloraxis_showscale=False,
        legend=dict(
            bgcolor="rgba(0,0,0,0.3)",
            bordercolor=BORDA,
            borderwidth=1,
            font=dict(color=TEXTO2, size=12),
        ),
        hoverlabel=dict(
            bgcolor=BG_PLOT,
            bordercolor=BORDA,
            font=dict(color=TEXTO, size=13),
        ),
    )
    base.update(extra)
    return base


def _empty_fig(mensagem: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=f"<b>{mensagem}</b>",
        showarrow=False,
        font=dict(size=15, color=TEXTO2, family=_FONTE["family"]),
        xref="paper", yref="paper",
        x=0.5, y=0.5,
    )
    fig.update_layout(**_layout(height=280))
    return fig


def _fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ── 1. Treemap de despesas ──────────────────────────────────────
def plot_despesas_categoria(df: pd.DataFrame, nome_dep: str = "") -> go.Figure:
    """Treemap colorido e legível das despesas CEAP por categoria."""
    if df.empty or "tipoDespesa" not in df.columns:
        return _empty_fig("Sem dados de despesas para este período")

    df_copy = df.copy()
    df_copy["valorLiquido"] = pd.to_numeric(
        df_copy.get("valorLiquido", 0), errors="coerce"
    ).fillna(0.0)
    df_copy = df_copy[df_copy["valorLiquido"] > 0]

    if df_copy.empty:
        return _empty_fig("Nenhuma despesa com valor positivo encontrada")

    agrupado = (
        df_copy.groupby("tipoDespesa", as_index=False)
        .agg(total=("valorLiquido", "sum"), qtd=("valorLiquido", "count"))
        .sort_values("total", ascending=False)
    )
    total_geral = agrupado["total"].sum()
    agrupado["pct"] = (agrupado["total"] / total_geral * 100).round(1)
    agrupado["label"] = agrupado.apply(
        lambda r: f"{r['tipoDespesa']}<br><b>{_fmt_brl(r['total'])}</b><br>{r['pct']}%", axis=1
    )

    fig = px.treemap(
        agrupado,
        path=["tipoDespesa"],
        values="total",
        title=f"💰 Distribuição de Despesas CEAP",
        color="tipoDespesa",
        color_discrete_sequence=CORES_CATEGORIAS,
        custom_data=["total", "pct", "qtd"],
    )
    fig.update_traces(
        texttemplate=(
            "<b>%{label}</b><br>"
            "%{customdata[1]:.1f}%"
        ),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Total: <b>R$ %{value:,.2f}</b><br>"
            "Participação: <b>%{customdata[1]:.1f}%</b><br>"
            "Notas: <b>%{customdata[2]}</b><extra></extra>"
        ),
        textfont=dict(size=13, color="white", family=_FONTE["family"]),
        marker=dict(line=dict(color=BG_CARD, width=3)),
    )
    fig.update_layout(
        **_layout(height=420),
        title=dict(
            text=f"💰 Despesas CEAP — <b>{nome_dep}</b>",
            font=dict(size=16, color=TEXTO),
            x=0,
        ),
    )
    return fig


# ── 2. Gráfico de votações por mês ─────────────────────────────
def plot_votacoes_timeline(df: pd.DataFrame, nome_dep: str = "") -> go.Figure:
    """Barras horizontais com ranking de participação mensal."""
    if df.empty or "dataVotacao" not in df.columns:
        return _empty_fig("Sem dados de votações para este período")

    df_copy = df.copy()
    df_copy["dataVotacao"] = pd.to_datetime(df_copy["dataVotacao"], errors="coerce")
    df_copy = df_copy.dropna(subset=["dataVotacao"])

    if df_copy.empty:
        return _empty_fig("Datas de votação inválidas")

    df_copy["mes"] = df_copy["dataVotacao"].dt.to_period("M").astype(str)
    contagem = (
        df_copy.groupby("mes").size()
        .reset_index(name="votacoes")
        .sort_values("mes")
    )

    # Colorir barras pelo volume (mais escuro = mais votações)
    max_v = contagem["votacoes"].max()
    contagem["cor"] = contagem["votacoes"].apply(
        lambda v: AZUL if v >= max_v * 0.7
        else (VERDE if v >= max_v * 0.4 else TEXTO2)
    )

    fig = go.Figure(
        go.Bar(
            x=contagem["mes"],
            y=contagem["votacoes"],
            marker=dict(
                color=contagem["cor"],
                line=dict(color=BG_CARD, width=1),
                opacity=0.9,
            ),
            text=contagem["votacoes"],
            textposition="outside",
            textfont=dict(color=TEXTO, size=12),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Votações: <b>%{y}</b><extra></extra>"
            ),
        )
    )
    fig.update_layout(
        **_layout(height=380),
        title=dict(
            text=f"🗳️ Participação em Votações — <b>{nome_dep}</b>",
            font=dict(size=16),
            x=0,
        ),
        xaxis=dict(
            tickangle=-40,
            gridcolor=BORDA,
            tickfont=dict(color=TEXTO2, size=11),
            title="",
            linecolor=BORDA,
        ),
        yaxis=dict(
            gridcolor=BORDA,
            tickfont=dict(color=TEXTO2, size=11),
            title="Votações",
            titlefont=dict(color=TEXTO2),
            linecolor=BORDA,
        ),
    )
    return fig


# ── 3. Tabela de ranking dos deputados ─────────────────────────
def plot_ranking_deputados(deputados: list[dict]) -> go.Figure:
    """Tabela premium com lista de deputados filtrados."""
    if not deputados:
        return _empty_fig("Nenhum deputado encontrado com os filtros aplicados")

    df = pd.DataFrame(deputados)
    colunas_map = {
        "nome": "👤 Nome",
        "siglaPartido": "🎖️ Partido",
        "siglaUf": "🗺️ UF",
        "email": "✉️ E-mail",
    }
    colunas = [c for c in colunas_map if c in df.columns]
    df_disp = df[colunas].rename(columns=colunas_map).fillna("—")

    n = len(df_disp)
    fill_colors = [
        [BG_PLOT if i % 2 == 0 else BG_CARD for i in range(n)]
        for _ in df_disp.columns
    ]

    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[280, 90, 60, 260],
                header=dict(
                    values=[f"<b>{c}</b>" for c in df_disp.columns],
                    fill_color=AZUL,
                    font=dict(color="white", size=13, family=_FONTE["family"]),
                    align="left",
                    height=40,
                    line=dict(color=BG_CARD, width=2),
                ),
                cells=dict(
                    values=[df_disp[c].tolist() for c in df_disp.columns],
                    fill_color=fill_colors,
                    font=dict(color=TEXTO, size=12, family=_FONTE["family"]),
                    align="left",
                    height=32,
                    line=dict(color=BORDA, width=1),
                ),
            )
        ]
    )
    fig.update_layout(
        paper_bgcolor=BG_CARD,
        margin=dict(t=5, l=0, r=0, b=5),
        height=min(680, 80 + n * 33),
    )
    return fig


# ── 4. Gauge de participação ────────────────────────────────────
def plot_gauge_participacao(votacoes: int, total_esperado: int = 300) -> go.Figure:
    """Velocímetro de taxa de participação em votações."""
    pct = min((votacoes / total_esperado) * 100, 100) if total_esperado > 0 else 0
    cor = VERDE if pct >= 75 else (AMARELO if pct >= 40 else VERMELHO)
    label_status = (
        "Alta participação ✅" if pct >= 75
        else ("Participação moderada ⚠️" if pct >= 40
              else "Baixa participação 🔴")
    )

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=votacoes,
            number=dict(
                font=dict(color=cor, size=36, family=_FONTE["family"]),
                suffix=" votos",
            ),
            title=dict(
                text=f"<b>Presença em Plenário</b><br><span style='font-size:13px;color:{TEXTO2}'>{label_status}</span>",
                font=dict(color=TEXTO, size=15, family=_FONTE["family"]),
            ),
            gauge=dict(
                axis=dict(
                    range=[0, total_esperado],
                    tickcolor=TEXTO2,
                    tickfont=dict(color=TEXTO2, size=11),
                    nticks=6,
                ),
                bar=dict(color=cor, thickness=0.7),
                bgcolor=BG_PLOT,
                borderwidth=2,
                bordercolor=BORDA,
                steps=[
                    dict(range=[0, total_esperado * 0.4], color="#2D1B1B"),
                    dict(range=[total_esperado * 0.4, total_esperado * 0.75], color="#2D2B1B"),
                    dict(range=[total_esperado * 0.75, total_esperado], color="#1B2D1B"),
                ],
                threshold=dict(
                    line=dict(color=TEXTO2, width=2),
                    thickness=0.8,
                    value=total_esperado * 0.75,
                ),
            ),
        )
    )
    fig.update_layout(
        paper_bgcolor=BG_CARD,
        font=dict(color=TEXTO, family=_FONTE["family"]),
        height=260,
        margin=dict(t=50, b=10, l=30, r=30),
    )
    return fig


# ── 5. Donut de participação por partido ───────────────────────
def plot_donut_partidos(deputados: list[dict]) -> go.Figure:
    """Gráfico donut com distribuição de deputados por partido."""
    if not deputados:
        return _empty_fig("Sem dados de partidos")

    df = pd.DataFrame(deputados)
    if "siglaPartido" not in df.columns:
        return _empty_fig("Dados de partido indisponíveis")

    contagem = (
        df["siglaPartido"].value_counts()
        .reset_index()
        .rename(columns={"index": "partido", "siglaPartido": "total"})
        .head(15)  # Top 15 partidos
    )
    # Compatibilidade com diferentes versões do Pandas
    if "siglaPartido" in contagem.columns and "count" not in contagem.columns:
        contagem.columns = ["partido", "total"]
    elif "count" in contagem.columns:
        contagem.columns = ["partido", "total"]

    fig = go.Figure(
        go.Pie(
            labels=contagem.iloc[:, 0],
            values=contagem.iloc[:, 1],
            hole=0.55,
            marker=dict(
                colors=CORES_CATEGORIAS[:len(contagem)],
                line=dict(color=BG_CARD, width=2),
            ),
            textfont=dict(size=12, color="white"),
            hovertemplate="<b>%{label}</b><br>Deputados: <b>%{value}</b><br>%{percent}<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor=BG_CARD,
        plot_bgcolor=BG_PLOT,
        font=dict(color=TEXTO, family=_FONTE["family"], size=13),
        title=dict(text="🎖️ Distribuição por Partido", font=dict(size=16, color=TEXTO), x=0),
        height=380,
        margin=dict(t=55, l=10, r=10, b=10),
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1.02, y=0.5,
            font=dict(color=TEXTO2, size=11),
            bgcolor="rgba(0,0,0,0.3)",
            bordercolor=BORDA,
            borderwidth=1,
        ),
        hoverlabel=dict(bgcolor=BG_PLOT, bordercolor=BORDA, font=dict(color=TEXTO, size=13)),
        annotations=[dict(
            text=f"<b>{len(df)}</b><br><span style='font-size:11px'>deputados</span>",
            x=0.5, y=0.5,
            font=dict(size=18, color=TEXTO, family=_FONTE["family"]),
            showarrow=False,
        )],
    )
    return fig


# ── 6. Timeline de discursos ────────────────────────────────────
def plot_discursos_timeline(df: pd.DataFrame, nome_dep: str = "") -> go.Figure:
    """Barras mensais de discursos em plenário."""
    if df.empty or "dataHoraInicio" not in df.columns:
        return _empty_fig("Nenhum discurso registrado neste período")

    df_copy = df.copy()
    df_copy["dataHoraInicio"] = pd.to_datetime(df_copy["dataHoraInicio"], errors="coerce")
    df_copy = df_copy.dropna(subset=["dataHoraInicio"])

    if df_copy.empty:
        return _empty_fig("Datas de discursos inválidas")

    df_copy["mes"] = df_copy["dataHoraInicio"].dt.to_period("M").astype(str)
    contagem = df_copy.groupby("mes").size().reset_index(name="qtd").sort_values("mes")

    fig = go.Figure(
        go.Bar(
            x=contagem["mes"],
            y=contagem["qtd"],
            marker=dict(
                color=VERDE,
                line=dict(color=BG_CARD, width=1),
                opacity=0.85,
            ),
            text=contagem["qtd"],
            textposition="outside",
            textfont=dict(color=TEXTO, size=12),
            hovertemplate="<b>%{x}</b><br>Discursos: <b>%{y}</b><extra></extra>",
        )
    )
    fig.update_layout(
        **_layout(height=340),
        title=dict(
            text=f"🎙️ Discursos em Plenário — <b>{nome_dep}</b>",
            font=dict(size=16), x=0,
        ),
        xaxis=dict(tickangle=-40, gridcolor=BORDA, tickfont=dict(color=TEXTO2, size=11),
                   title="", linecolor=BORDA),
        yaxis=dict(gridcolor=BORDA, tickfont=dict(color=TEXTO2, size=11),
                   title="Discursos", titlefont=dict(color=TEXTO2), linecolor=BORDA),
    )
    return fig


# ── 7. Presença em eventos por tipo ────────────────────────────
def plot_eventos_presenca(df: pd.DataFrame, nome_dep: str = "") -> go.Figure:
    """Distribuição de eventos por tipo de sessão."""
    if df.empty or "descricaoTipo" not in df.columns:
        return _empty_fig("Nenhum evento registrado neste período")

    contagem = (
        df["descricaoTipo"].value_counts()
        .reset_index()
    )
    # Garantir nomes de colunas independente da versão do pandas
    contagem.columns = ["tipo", "qtd"]
    contagem = contagem.head(10)

    fig = go.Figure(
        go.Bar(
            x=contagem["qtd"],
            y=contagem["tipo"],
            orientation="h",
            marker=dict(
                color=CORES_CATEGORIAS[:len(contagem)],
                line=dict(color=BG_CARD, width=1),
            ),
            text=contagem["qtd"],
            textposition="outside",
            textfont=dict(color=TEXTO, size=12),
            hovertemplate="<b>%{y}</b><br>Eventos: <b>%{x}</b><extra></extra>",
        )
    )
    fig.update_layout(
        **_layout(height=min(420, 120 + len(contagem) * 38)),
        title=dict(
            text=f"📅 Presença em Eventos — <b>{nome_dep}</b>",
            font=dict(size=16), x=0,
        ),
        xaxis=dict(gridcolor=BORDA, tickfont=dict(color=TEXTO2, size=11),
                   title="Eventos", titlefont=dict(color=TEXTO2)),
        yaxis=dict(gridcolor=BORDA, tickfont=dict(color=TEXTO2, size=11),
                   title="", autorange="reversed"),
    )
    return fig


# ── 8. Tabela de órgãos/comissões ──────────────────────────────
def plot_orgaos_table(orgaos: list[dict]) -> go.Figure:
    """Tabela premium de comissões e órgãos do deputado."""
    if not orgaos:
        return _empty_fig("Deputado não participa de órgãos registrados")

    df = pd.DataFrame(orgaos)

    colunas_map = {
        "siglaOrgao":  "🏛️ Sigla",
        "nomeOrgao":   "📋 Órgão / Comissão",
        "titulo":      "🎫 Cargo",
        "dataInicio":  "📅 Início",
        "dataFim":     "🏁 Fim",
    }
    cols = [c for c in colunas_map if c in df.columns]
    df_disp = df[cols].rename(columns=colunas_map).fillna("—")

    # Formatar datas
    for col in ["📅 Início", "🏁 Fim"]:
        if col in df_disp.columns:
            df_disp[col] = pd.to_datetime(
                df_disp[col], errors="coerce"
            ).dt.strftime("%d/%m/%Y").fillna("—")

    # Highlight linha ainda ativa (sem dataFim)
    n = len(df_disp)
    is_active = df["dataFim"].isna() if "dataFim" in df.columns else [False] * n
    AZUL_ALPHA = "rgba(59,130,246,0.20)"  # #3B82F6 com 20% de opacidade
    fill = [
        [AZUL_ALPHA if is_active.iloc[i] else (BG_PLOT if i % 2 == 0 else BG_CARD)
         for i in range(n)]
        for _ in df_disp.columns
    ]

    col_widths = [60, 350, 160, 90, 90][:len(df_disp.columns)]
    fig = go.Figure(go.Table(
        columnwidth=col_widths,
        header=dict(
            values=[f"<b>{c}</b>" for c in df_disp.columns],
            fill_color=AZUL,
            font=dict(color="white", size=13, family=_FONTE["family"]),
            align="left", height=40,
            line=dict(color=BG_CARD, width=2),
        ),
        cells=dict(
            values=[df_disp[c].tolist() for c in df_disp.columns],
            fill_color=fill,
            font=dict(color=TEXTO, size=12, family=_FONTE["family"]),
            align="left", height=32,
            line=dict(color=BORDA, width=1),
        ),
    ))
    fig.update_layout(
        paper_bgcolor=BG_CARD,
        margin=dict(t=5, l=0, r=0, b=5),
        height=min(640, 80 + n * 33),
    )
    return fig


# ── 9. Tabela de frentes parlamentares ─────────────────────────
def plot_frentes_table(frentes: list[dict]) -> go.Figure:
    """Tabela compacta das frentes parlamentares do deputado."""
    if not frentes:
        return _empty_fig("Deputado não participa de frentes parlamentares registradas")

    df = pd.DataFrame(frentes).fillna("—")

    colunas_map = {
        "titulo":        "🏳️ Frente Parlamentar",
        "idLegislatura": "📜 Legislatura",
    }
    cols = [c for c in colunas_map if c in df.columns]
    df_disp = df[cols].rename(columns=colunas_map)

    n = len(df_disp)
    fill = [
        [BG_PLOT if i % 2 == 0 else BG_CARD for i in range(n)]
        for _ in df_disp.columns
    ]

    fig = go.Figure(go.Table(
        columnwidth=[500, 100],
        header=dict(
            values=[f"<b>{c}</b>" for c in df_disp.columns],
            fill_color=AMARELO,
            font=dict(color=BG_CARD, size=13, family=_FONTE["family"]),
            align="left", height=40,
            line=dict(color=BG_CARD, width=2),
        ),
        cells=dict(
            values=[df_disp[c].tolist() for c in df_disp.columns],
            fill_color=fill,
            font=dict(color=TEXTO, size=12, family=_FONTE["family"]),
            align="left", height=30,
            line=dict(color=BORDA, width=1),
        ),
    ))
    fig.update_layout(
        paper_bgcolor=BG_CARD,
        margin=dict(t=5, l=0, r=0, b=5),
        height=min(620, 80 + n * 31),
    )
    return fig

