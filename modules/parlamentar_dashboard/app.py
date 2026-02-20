"""
Dashboard interativo de dados parlamentares — Módulo 4.
Execute com: poetry run streamlit run modules/parlamentar_dashboard/app.py

Endpoints utilizados: /deputados, /deputados/{id}, /deputados/{id}/despesas,
/deputados/{id}/discursos, /deputados/{id}/eventos, /deputados/{id}/orgaos,
/deputados/{id}/frentes, /partidos
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from datetime import datetime

from modules.parlamentar_dashboard.data_loader import (
    get_deputados,
    get_deputado_detail,
    get_despesas,
    get_discursos,
    get_eventos,
    get_orgaos,
    get_frentes_deputado,
    get_partidos,
    get_ufs,
    calcular_total_despesas,
)
from modules.parlamentar_dashboard.charts import (
    plot_despesas_categoria,
    plot_ranking_deputados,
    plot_donut_partidos,
    plot_discursos_timeline,
    plot_eventos_presenca,
    plot_orgaos_table,
    plot_frentes_table,
    plot_gauge_participacao,
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
.stApp {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background-color: #0f1117;
    color: #e0e0e0;
}
p, h1, h2, h3, h4, h5, h6, label,
div[data-testid="stMarkdownContainer"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* ─ Sidebar ─ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #1a1f2e 100%);
    border-right: 1px solid #374151;
}

/* ─ Tabs externas ─ */
.stTabs [data-baseweb="tab-list"] {
    background: #111827;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #9CA3AF;
    border-radius: 8px;
    font-weight: 500;
    padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
    background: #3B82F6 !important;
    color: white !important;
    font-weight: 600 !important;
}

/* ─ Métricas ─ */
[data-testid="stMetric"] {
    background: #111827;
    border: 1px solid #374151;
    border-radius: 12px;
    padding: 18px 22px;
    transition: box-shadow 0.2s;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 4px 20px rgba(59, 130, 246, 0.15);
}
[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #3B82F6 !important;
}
[data-testid="stMetricLabel"] {
    color: #9CA3AF !important;
    font-size: 0.85rem !important;
}

/* ─ Botão primário ─ */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 10px 24px;
    transition: all 0.2s ease;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

/* ─ Botão secundário (Limpar Cache) ─ */
.stButton > button[kind="secondary"] {
    background: transparent;
    color: #9CA3AF;
    border: 1px solid #374151;
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #3B82F6;
    color: #3B82F6;
}

/* ─ Selectboxes ─ */
div[data-baseweb="select"] > div {
    background: #111827 !important;
    border-color: #374151 !important;
    color: white !important;
}

/* ─ Divisores e alerts ─ */
hr { border-color: #374151; margin: 1.5rem 0; }
.stAlert { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────
def _fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ── Session state ──────────────────────────────────────────────
for key, default in {
    "analise_feita": False,
    "analise_dep_id": None,
    "analise_dados": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


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
        
        Dados: [API Dados Abertos](https://dadosabertos.camara.leg.br)
        
        🔄 Cache: 1h (listas) / 30min (análises)
        """)

    if st.button("🗑️ Limpar Cache", help="Força atualização de todos os dados"):
        st.cache_data.clear()
        st.session_state.analise_feita = False
        st.session_state.analise_dados = {}
        st.toast("Cache limpo!", icon="✅")


# ══ Abas Principais ═════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["👥 Deputados", "🔍 Análise Individual", "ℹ️ Sobre"])


# ─── Aba 1: Lista de Deputados ──────────────────────────────────
with tab1:
    st.subheader("Deputados Federais")

    with st.spinner("Buscando todos os deputados..."):
        deputados = get_deputados(uf=uf_param, partido=partido_param)

    if not deputados:
        st.warning("Nenhum deputado encontrado. Tente outros filtros.", icon="🔍")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("👤 Deputados", len(deputados))
        partidos_unicos = len({d.get("siglaPartido") for d in deputados if d.get("siglaPartido")})
        c2.metric("🎖️ Partidos", partidos_unicos)
        ufs_unicas = len({d.get("siglaUf") for d in deputados if d.get("siglaUf")})
        c3.metric("🗺️ Estados", ufs_unicas)

        st.divider()

        col_tab, col_donut = st.columns([3, 2])
        with col_tab:
            st.caption(f"📋 Lista completa — {len(deputados)} deputados")
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

        col_sel, col_btn = st.columns([5, 1])
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

        # Guard: nome_sel pode ser None se opcoes estiver vazio
        if not dep_id:
            st.info("Selecione um deputado e clique em Analisar.", icon="👆")
        elif analisar or (st.session_state.analise_feita and st.session_state.analise_dep_id == dep_id):
            if analisar or not st.session_state.analise_dados:
                # Ano padrão: current – 1 (mais completo)
                ano = ano_atual - 1

                with st.status("Carregando dados do parlamentar...", expanded=True) as status:
                    st.write("📄 Dados cadastrais...")
                    detalhes = get_deputado_detail(dep_id)

                    st.write(f"💰 Despesas CEAP ({ano})...")
                    df_desp = get_despesas(dep_id, ano)

                    st.write(f"🎙️ Discursos ({ano})...")
                    df_disc = get_discursos(dep_id, ano)

                    st.write(f"📅 Eventos ({ano})...")
                    df_eventos = get_eventos(dep_id, ano)

                    st.write("🏛️ Órgãos e comissões...")
                    orgaos = get_orgaos(dep_id)

                    st.write("🏳️ Frentes parlamentares...")
                    frentes = get_frentes_deputado(dep_id)

                    status.update(label="✅ Dados carregados!", state="complete", expanded=False)

                st.session_state.analise_feita = True
                st.session_state.analise_dep_id = dep_id
                st.session_state.analise_dados = {
                    "detalhes": detalhes, "df_desp": df_desp,
                    "df_disc": df_disc, "df_eventos": df_eventos,
                    "orgaos": orgaos, "frentes": frentes, "ano": ano,
                }
            else:
                d = st.session_state.analise_dados
                detalhes   = d["detalhes"]
                df_desp    = d["df_desp"]
                df_disc    = d["df_disc"]
                df_eventos = d["df_eventos"]
                orgaos     = d["orgaos"]
                frentes    = d["frentes"]
                ano        = d.get("ano", ano_atual - 1)

            # ── Perfil ────────────────────────────────────────
            dados_dep = detalhes.get("ultimoStatus", {}) if detalhes else {}

            col_foto, col_info = st.columns([1, 4])
            with col_foto:
                foto = dados_dep.get("urlFoto")
                if foto:
                    st.image(foto, width=130)
                else:
                    st.markdown("## 👤")

            with col_info:
                nome_oficial = dados_dep.get("nome", nome_sel)
                st.markdown(f"### {nome_oficial}")
                ic1, ic2, ic3 = st.columns(3)
                ic1.markdown(f"**🎖️ Partido**\n\n{dados_dep.get('siglaPartido', '—')}")
                ic2.markdown(f"**🗺️ Estado**\n\n{dados_dep.get('siglaUf', '—')}")
                gab = dados_dep.get("gabinete") or {}
                ic3.markdown(f"**🏢 Gabinete**\n\nPrédio {gab.get('predio', '—')}, Sala {gab.get('sala', '—')}")
                email = dados_dep.get("email") or "—"
                st.caption(f"✉️ {email}")

            st.info(
                f"📅 Dados do ano **{ano}** "
                f"— o mais recente com informações completas.",
                icon="ℹ️",
            )
            st.divider()

            # ── Métricas de atividade ─────────────────────────
            total_desp = calcular_total_despesas(df_desp)
            total_notas = len(df_desp)
            total_disc = len(df_disc)
            total_eventos = len(df_eventos)
            total_orgaos = len(orgaos)
            total_frentes = len(frentes)

            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("💰 Gasto CEAP", _fmt_brl(total_desp))
            m2.metric("🧾 Notas Fiscais", total_notas)
            m3.metric("🎙️ Discursos", total_disc)
            m4.metric("📅 Eventos", total_eventos)
            m5.metric("🏛️ Comissões", total_orgaos)
            m6.metric("🏳️ Frentes", total_frentes)

            st.divider()

            # ── Abas de visualização ──────────────────────────
            sub1, sub2, sub3, sub4, sub5 = st.tabs([
                "💰 Despesas CEAP",
                "🎙️ Discursos",
                "📅 Eventos",
                "🏛️ Órgãos",
                "🏳️ Frentes",
            ])

            with sub1:
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.plotly_chart(
                        plot_despesas_categoria(df_desp, nome_oficial),
                        width="stretch",
                    )
                with col_g2:
                    st.plotly_chart(
                        plot_gauge_participacao(total_notas, total_esperado=500),
                        width="stretch",
                    )

                if not df_desp.empty:
                    with st.expander("📋 Ver detalhamento completo das despesas"):
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

            with sub2:
                st.plotly_chart(
                    plot_discursos_timeline(df_disc, nome_oficial),
                    width="stretch",
                )
                if not df_disc.empty and "tipoDiscurso" in df_disc.columns:
                    with st.expander("📋 Ver lista de discursos"):
                        cols_d = [c for c in ["dataHoraInicio", "tipoDiscurso", "sumario", "urlTexto"]
                                  if c in df_disc.columns]
                        st.dataframe(df_disc[cols_d], width="stretch", height=350)

            with sub3:
                st.plotly_chart(
                    plot_eventos_presenca(df_eventos, nome_oficial),
                    width="stretch",
                )
                if not df_eventos.empty:
                    with st.expander("📋 Ver lista de eventos"):
                        cols_e = [c for c in ["dataHoraInicio", "situacao", "descricaoTipo", "descricao"]
                                  if c in df_eventos.columns]
                        st.dataframe(df_eventos[cols_e], width="stretch", height=350)

            with sub4:
                st.caption(f"🏛️ {total_orgaos} órgão(s) e comissão(es) registrados. Linhas azul-claro = mandato ativo.")
                st.plotly_chart(
                    plot_orgaos_table(orgaos),
                    width="stretch",
                )

            with sub5:
                st.caption(f"🏳️ {total_frentes} frente(s) parlamentar(es) registrada(s).")
                st.plotly_chart(
                    plot_frentes_table(frentes),
                    width="stretch",
                )


# ─── Aba 3: Sobre ───────────────────────────────────────────────
with tab3:
    st.subheader("ℹ️ Sobre o Câmara Analytics")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        ### 🏛️ O que é?
        O **Câmara Analytics** faz parte do **Sistema Modular de Análise de Dados da Câmara dos Deputados**.

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
        | Lista de deputados | `GET /deputados` |
        | Detalhe do deputado | `GET /deputados/{id}` |
        | Despesas CEAP | `GET /deputados/{id}/despesas` |
        | Discursos | `GET /deputados/{id}/discursos` |
        | Presença em eventos | `GET /deputados/{id}/eventos` |
        | Órgãos/comissões | `GET /deputados/{id}/orgaos` |
        | Frentes parlamentares | `GET /deputados/{id}/frentes` |
        | Lista de partidos | `GET /partidos` |

        ### 📊 Cache Configurado
        - **Listas** (deputados, partidos): **1 hora**
        - **Análises individuais**: **30 minutos**

        ---
        Fonte: [API de Dados Abertos da Câmara](https://dadosabertos.camara.leg.br)
        """)
