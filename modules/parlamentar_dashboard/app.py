"""
Dashboard interativo de dados parlamentares — Módulo 4.
Execute com: poetry run streamlit run modules/parlamentar_dashboard/app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from datetime import datetime

from modules.parlamentar_dashboard.data_loader import (
    get_deputados,
    get_deputado_detail,
    get_votacoes,
    get_despesas,
    get_partidos,
    get_ufs,
    calcular_total_despesas,
)
from modules.parlamentar_dashboard.charts import (
    plot_despesas_categoria,
    plot_votacoes_timeline,
    plot_ranking_deputados,
    plot_gauge_participacao,
    plot_donut_partidos,
)

# ── Configuração da Página ──────────────────────────────────────
st.set_page_config(
    page_title="Câmara Analytics",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://dadosabertos.camara.leg.br",
        "About": "Sistema Modular de Análise de Dados da Câmara dos Deputados",
    },
)

# ── CSS Personalizado ──────────────────────────────────────────
st.markdown("""
<style>
/* ─ Fundo e texto global ─ */
.stApp {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background-color: #0f1117;
    color: #e0e0e0;
}
p, h1, h2, h3, h4, h5, h6, label, span.st-emotion-cache-1629p8f, div[data-testid="stMarkdownContainer"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* ─ Sidebar ─ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    border-right: 1px solid #2a2a3e;
}

/* ─ Tabs ─ */
.stTabs [data-baseweb="tab-list"] {
    background: #1a1a2e;
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #888;
    border-radius: 6px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: #4A90D9 !important;
    color: white !important;
}

/* ─ Métricas ─ */
[data-testid="stMetric"] {
    background: #1a1a2e;
    border: 1px solid #2a2a3e;
    border-radius: 10px;
    padding: 16px 20px;
}
[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #4A90D9 !important;
}
[data-testid="stMetricLabel"] { color: #888 !important; font-size: 0.85rem !important; }

/* ─ Botões ─ */
.stButton > button {
    background: linear-gradient(135deg, #4A90D9 0%, #2c5aa0 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 10px 24px;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(74, 144, 217, 0.4);
}

/* ─ Selectboxes ─ */
div[data-baseweb="select"] > div {
    background: #1a1a2e !important;
    border-color: #2a2a3e !important;
    color: white !important;
}

/* ─ Divisores ─ */
hr { border-color: #2a2a3e; margin: 1.5rem 0; }

/* ─ Info/Warning boxes ─ */
.stAlert { border-radius: 8px; }

/* ─ Spinner ─ */
.stSpinner > div { border-top-color: #4A90D9 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helper de formatação ────────────────────────────────────────
def _fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ── Inicializar session_state ───────────────────────────────────
if "analise_feita" not in st.session_state:
    st.session_state.analise_feita = False
if "analise_dep_id" not in st.session_state:
    st.session_state.analise_dep_id = None
if "analise_dados" not in st.session_state:
    st.session_state.analise_dados = {}


# ══ Header ══════════════════════════════════════════════════════
st.markdown("# 🏛️ Câmara Analytics")
st.caption("Sistema de Análise de Dados da Câmara dos Deputados do Brasil")

st.divider()


# ══ Sidebar ═════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Filtros")
    st.caption("Filtre os dados exibidos no dashboard")

    ano_atual = datetime.now().year

    with st.spinner("Carregando UFs..."):
        ufs = get_ufs()
    uf = st.selectbox("🗺️ Estado (UF)", options=["Todos"] + ufs, index=0)
    uf_param = None if uf == "Todos" else uf

    with st.spinner("Carregando partidos..."):
        partidos = get_partidos()
    partido = st.selectbox("🎖️ Partido", options=["Todos"] + partidos, index=0)
    partido_param = None if partido == "Todos" else partido

    st.divider()

    with st.expander("ℹ️ Sobre"):
        st.markdown("""
        **Câmara Analytics v1.0**
        
        Dados fornecidos pela [API de Dados Abertos](https://dadosabertos.camara.leg.br) da Câmara dos Deputados.
        
        🔄 Cache: 1h (listas) / 30min (dados individuais)
        """)

    if st.button("🗑️ Limpar Cache", help="Força atualização de todos os dados"):
        st.cache_data.clear()
        st.session_state.analise_feita = False
        st.toast("Cache limpo com sucesso!", icon="✅")


# ══ Abas Principais ═════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["👥 Deputados", "🔍 Análise Individual", "ℹ️ Sobre"])


# ─── Aba 1: Lista de Deputados ──────────────────────────────────
with tab1:
    st.subheader(f"Deputados Federais")

    with st.spinner("Buscando deputados na API..."):
        deputados = get_deputados(uf=uf_param, partido=partido_param)

    if not deputados:
        st.warning("Nenhum deputado encontrado. Tente outros filtros.", icon="🔍")
    else:
        # Métricas
        c1, c2, c3 = st.columns(3)
        c1.metric("👤 Deputados", len(deputados))
        partidos_unicos = len({d.get("siglaPartido") for d in deputados if d.get("siglaPartido")})
        c2.metric("🎖️ Partidos", partidos_unicos)
        ufs_unicas = len({d.get("siglaUf") for d in deputados if d.get("siglaUf")})
        c3.metric("🗺️ Estados", ufs_unicas)

        st.divider()

        col_tab, col_donut = st.columns([3, 2])
        with col_tab:
            st.caption(f"📋 Lista completa — {len(deputados)} deputados encontrados")
            st.plotly_chart(plot_ranking_deputados(deputados), width="stretch")
        with col_donut:
            st.plotly_chart(plot_donut_partidos(deputados), width="stretch")



# ─── Aba 2: Análise Individual ──────────────────────────────────
with tab2:
    st.subheader("Análise Individual do Parlamentar")

    with st.spinner("Carregando lista de deputados..."):
        lista_base = get_deputados(uf=uf_param, partido=partido_param)

    if not lista_base:
        st.warning("Nenhum deputado disponível. Ajuste os filtros na sidebar.", icon="⚠️")
    else:
        opcoes = {dep["nome"]: dep["id"] for dep in lista_base if dep.get("nome")}

        col_sel, col_btn = st.columns([4, 1])
        with col_sel:
            nome_sel = st.selectbox(
                "Selecione o Deputado",
                options=sorted(opcoes.keys()),
                label_visibility="collapsed",
                placeholder="🔎 Digite o nome do deputado...",
            )
        with col_btn:
            analisar = st.button("🔎 Analisar", type="primary")

        dep_id = opcoes.get(nome_sel)

        # Disparar análise (ou reusar session_state se mesmo deputado)
        if analisar or (st.session_state.analise_feita and st.session_state.analise_dep_id == dep_id):
            if analisar or not st.session_state.analise_dados:
                with st.status("Buscando dados do parlamentar...", expanded=True) as status:
                    st.write("📄 Carregando dados cadastrais...")
                    detalhes = get_deputado_detail(dep_id)

                    # Usar o ano anterior como padrão (mais completo na API)
                    ano_detectado = ano_atual - 1

                    st.write(f"💰 Buscando despesas CEAP de {ano_detectado}...")
                    df_desp = get_despesas(dep_id, ano_detectado)

                    st.write(f"🗳️ Carregando votações de {ano_detectado}...")
                    df_vot = get_votacoes(dep_id, ano_detectado)

                    status.update(label=f"✅ Dados de {ano_detectado} carregados!", state="complete", expanded=False)

                # Salvar no session_state
                st.session_state.analise_feita = True
                st.session_state.analise_dep_id = dep_id
                st.session_state.analise_dados = {
                    "detalhes": detalhes,
                    "df_desp": df_desp,
                    "df_vot": df_vot,
                    "ano": ano_detectado,
                }
            else:
                # Reusar dados do session_state
                detalhes = st.session_state.analise_dados["detalhes"]
                df_desp = st.session_state.analise_dados["df_desp"]
                df_vot = st.session_state.analise_dados["df_vot"]
                ano_detectado = st.session_state.analise_dados.get("ano", ano_atual - 1)

            # Badge do ano exibido
            st.info(f"📅 Exibindo dados do ano **{ano_detectado}** — o mais recente com informações disponíveis para este parlamentar.", icon="ℹ️")

            st.divider()

            # ── Perfil do Deputado ────────────────────────────
            dados_dep = detalhes.get("ultimoStatus", {}) if detalhes else {}

            col_foto, col_info = st.columns([1, 4])
            with col_foto:
                foto_url = dados_dep.get("urlFoto")
                if foto_url:
                    st.image(foto_url, width=130)
                else:
                    st.markdown("### 👤")

            with col_info:
                nome_oficial = dados_dep.get("nome", nome_sel)
                st.markdown(f"### {nome_oficial}")

                info_col1, info_col2, info_col3 = st.columns(3)
                info_col1.markdown(f"**🎖️ Partido**\n\n{dados_dep.get('siglaPartido', '—')}")
                info_col2.markdown(f"**🗺️ Estado**\n\n{dados_dep.get('siglaUf', '—')}")
                gab = dados_dep.get("gabinete") or {}
                info_col3.markdown(f"**🏢 Gabinete**\n\nPrédio {gab.get('predio', '—')}, Sala {gab.get('sala', '—')}")

                email = dados_dep.get("email") or "—"
                st.caption(f"✉️ {email}")

            st.divider()

            # ── Métricas de Atividade ─────────────────────────
            total_desp = calcular_total_despesas(df_desp)
            total_vot = len(df_vot) if not df_vot.empty else 0

            m1, m2, m3 = st.columns(3)
            m1.metric(f"💰 Gasto CEAP {ano_detectado}", _fmt_brl(total_desp))
            m2.metric(f"🗳️ Votações {ano_detectado}", total_vot)

            notas_fiscal = len(df_desp) if not df_desp.empty else 0
            m3.metric("🧾 Notas Fiscais", notas_fiscal)

            st.divider()

            # ── Gráficos ──────────────────────────────────────
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.plotly_chart(
                    plot_despesas_categoria(df_desp, nome_oficial),
                    width="stretch",
                )
            with col_g2:
                st.plotly_chart(
                    plot_votacoes_timeline(df_vot, nome_oficial),
                    width="stretch",
                )

            # Gauge de participação
            st.plotly_chart(
                plot_gauge_participacao(total_vot),
                width="stretch",
            )

            # ── Tabela de despesas detalhadas ─────────────────
            if not df_desp.empty:
                with st.expander("📋 Ver despesas detalhadas"):
                    cols_show = [c for c in [
                        "tipoDespesa", "dataDocumento", "nomeFornecedor",
                        "valorDocumento", "valorLiquido",
                    ] if c in df_desp.columns]

                    df_show = df_desp[cols_show].copy()
                    if "valorLiquido" in df_show.columns:
                        df_show["valorLiquido"] = pd.to_numeric(
                            df_show["valorLiquido"], errors="coerce"
                        )
                    st.dataframe(
                        df_show.sort_values("valorLiquido", ascending=False)
                        if "valorLiquido" in df_show.columns else df_show,
                        width="stretch",
                        height=400,
                    )


# ─── Aba 3: Sobre ───────────────────────────────────────────────
with tab3:
    st.subheader("ℹ️ Sobre o Câmara Analytics")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        ### 🏛️ O que é?

        O **Câmara Analytics** é parte do **Sistema Modular de Análise de Dados da Câmara dos Deputados**, 
        um ecossistema Python para explorar dados públicos do poder legislativo brasileiro.

        ### 📦 Módulos do Sistema
        | Módulo | Função |
        |--------|--------|
        | `tracker_gastos` | Despesas CEAP (CSV/Parquet) |
        | `network_analyst` | Redes de influência política |
        | `legis_notifier` | Alertas via Telegram |
        | `parlamentar_dashboard` | **Este dashboard** |
        | `tema_miner` | NLP em ementas legislativas |
        """)

    with col_b:
        st.markdown("""
        ### 🔌 Endpoints da API Utilizados

        | Dado | Endpoint |
        |------|----------|
        | Lista de deputados | `/deputados` |
        | Detalhe do deputado | `/deputados/{id}` |
        | Despesas CEAP | `/deputados/{id}/despesas` |
        | Votações | `/deputados/{id}/votacoes` |
        | Lista de partidos | `/partidos` |

        ### 📊 Cache Configurado
        - **Listas** (deputados, partidos, UFs): **1 hora**
        - **Dados individuais** (despesas, votações): **30 minutos**
        - **Limpar cache**: botão na sidebar

        ---
        Fonte: [API de Dados Abertos da Câmara](https://dadosabertos.camara.leg.br)
        """)
