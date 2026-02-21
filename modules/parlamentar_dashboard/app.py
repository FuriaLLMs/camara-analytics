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
    get_proposicoes,
    calcular_total_despesas,
    get_ranking_gastos_global,
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
    plot_spending_ranking,
    plot_anomaly_bubbles,
    plot_ceap_limit_gauge,
    plot_efficiency_quadrants,
)
from modules.tracker_gastos.analyzer import (
    detect_outliers,
    check_ceap_usage,
    analyze_marketing_costs,
)
import importlib
from modules.tema_miner.ai_core import AICore
importlib.reload(importlib.import_module("modules.tema_miner.ai_core"))
from modules.tema_miner.cleaner import process_ementas
from modules.tema_miner.visualizer import generate_wordcloud
from modules.municipal_tracker.loader_municipal import MunicipalLoader

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

# ── Controle de Escopo (V5.0) ──────────────────────────────────
st.sidebar.markdown("### 🌐 Escopo de Transparência")
escopo = st.sidebar.selectbox(
    "Selecione o nível legislativo:",
    ["🇧🇷 Federal (Brasília)", "🏝️ Municipal (Florianópolis)"],
    index=0
)

# Global variables para os loaders
loader_mun = MunicipalLoader()

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
def _fmt_int(valor: int) -> str:
    """Formata inteiros com separador de milhar brasileiro."""
    return f"{valor:,}".replace(",", ".")

def _fmt_brl(valor: float) -> str:
    """Formata valores monetários no padrão brasileiro com segurança para NaN."""
    try:
        if pd.isna(valor) or valor is None:
            return "R$ 0,00"
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"


# ── Session state ──────────────────────────────────────────────
for key, default in {
    "analise_feita": False,
    "analise_dep_id": None,
    "analise_dados": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ══ Header ══════════════════════════════════════════════════════
if escopo == "🇧🇷 Federal (Brasília)":
    st.markdown("# 🏛️ Câmara Analytics")
    st.caption("Sistema de Análise de Dados da Câmara dos Deputados do Brasil")
else:
    st.markdown("# 🏝️ Florianópolis Analytics")
    st.caption("Monitoramento Legislativo da Câmara Municipal de Florianópolis (CMF)")
st.divider()


# ══ Sidebar ═════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Filtros")
    st.caption("Filtre os dados exibidos no dashboard")

    # Bug Hunt: Anos dinâmicos
    ano_atual = datetime.now().year
    anos_disponiveis = [ano_atual, ano_atual - 1, ano_atual - 2]

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


def main_federal():
    # ══ Abas Principais ═════════════════════════════════════════════
    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 Deputados", 
        "🔍 Análise Individual", 
        "🏆 Rankings & Auditoria",
        "ℹ️ Sobre"
    ])


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
                        dados_dep = detalhes.get("ultimoStatus", {}) if detalhes else {}

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

                        st.write("🚨 Auditoria e anomalias...")
                        df_desp_audit = df_desp.rename(columns={
                            "tipoDespesa": "categoria", 
                            "valorLiquido": "valor_liquido", 
                            "dataDocumento": "data_documento",
                            "nomeFornecedor": "fornecedor"
                        })
                        df_outliers = detect_outliers(df_desp_audit)
                        ceap_status = check_ceap_usage(df_desp_audit.rename(columns={"ano": "ano", "mes": "mes"}), dados_dep.get("siglaUf", "DF"))

                        st.write("📊 Produtividade Legislativa...")
                        prop = get_proposicoes(dep_id, ano)
                        qtd_prop = len(prop)
                        total_g = calcular_total_despesas(df_desp)
                        # Bug Hunt: ROI mais informativo para produção zero
                        roi = total_g / qtd_prop if qtd_prop > 0 else 0
                        
                        textos_ementas = [p.get("ementa", "") for p in prop if p.get("ementa")]
                        # Unir ementas para análise de complexidade média
                        texto_completo = " ".join(textos_ementas)
                        complexidade = AICore.calcular_indice_complexidade(texto_completo)
                        tokens_deputado = process_ementas(textos_ementas)
                        
                        # Chamadas reais do Gemini (Com Fallback e Cache Persistente)
                        resumo_ia = AICore.sumarizar_perfil_llm(tokens_deputado, dep_id)
                        
                        primeira_ementa = textos_ementas[0] if textos_ementas else ""
                        politiques = AICore.traduzir_politiques(primeira_ementa)
                        
                        # Sentimento - Pegar o discurso mais recente
                        ultimo_discurso = df_disc.iloc[0]["transcricao"] if not df_disc.empty else ""
                        sentimento = AICore.analisar_sentimento_llm(ultimo_discurso, dep_id)

                        status.update(label="✅ Dados carregados!", state="complete", expanded=False)

                    st.session_state.analise_feita = True
                    st.session_state.analise_dep_id = dep_id
                    st.session_state.analise_dados = {
                        "detalhes": detalhes, "df_desp": df_desp,
                        "df_disc": df_disc, "df_eventos": df_eventos,
                        "orgaos": orgaos, "frentes": frentes, "ano": ano,
                        "outliers": df_outliers, "ceap": ceap_status,
                        "qtd_prop": qtd_prop, "roi": roi,
                        "complexidade": complexidade,
                        "tokens": tokens_deputado,
                        "resumo_ia": resumo_ia,
                        "politiques": politiques,
                        "sentimento": sentimento
                    }
                else:
                    d = st.session_state.analise_dados
                    detalhes   = d["detalhes"]
                    df_desp    = d["df_desp"]
                    df_disc    = d["df_disc"]
                    df_eventos = d["df_eventos"]
                    orgaos     = d["orgaos"]
                    frentes    = d["frentes"]
                    df_outliers = d.get("outliers", pd.DataFrame())
                    ceap_status = d.get("ceap", {})
                    qtd_prop    = d.get("qtd_prop", 0)
                    roi         = d.get("roi", 0)
                    complexidade = d.get("complexidade", {"score": 0, "nivel": "N/A"})
                    tokens_deputado = d.get("tokens", [])
                    resumo_ia = d.get("resumo_ia", "Processando...")
                    politiques = d.get("politiques", "N/A")
                    sentimento = d.get("sentimento", "N/A")
                    ano        = d.get("ano", ano_atual - 1)

                # ── Perfil ────────────────────────────────────────

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

                st.divider()

                # Bug Hunt: Layout métricas (3x2 em telas pequenas é melhor do que 6 columns)
                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.metric("💰 Gasto CEAP", _fmt_brl(total_desp))
                    st.metric("📅 Eventos", total_eventos)
                with m_col2:
                    st.metric("🧾 Notas Fiscais", total_notas)
                    st.metric("🏛️ Comissões", total_orgaos)
                with m_col3:
                    st.metric("🎙️ Discursos", total_disc)
                    st.metric("🏳️ Frentes", total_frentes)

                st.divider()

                # ── Indicadores de Produção vs Gasto (V3.0)
                st.markdown("### 📊 Eficiência Legislativa")
                c_roi1, c_roi2, c_roi3 = st.columns(3)
                with c_roi1:
                    st.metric("📜 Proposições", _fmt_int(qtd_prop))
                with c_roi2:
                    # Gasto Total com formato BRL resumido ou completo
                    gasto_fmt = _fmt_brl(total_desp).replace(",00", "") 
                    st.metric("💰 Gasto Total", gasto_fmt)
                with c_roi3:
                    # ROI com formatação BRL correta
                    roi_label = _fmt_brl(roi).replace(",00", "") if roi > 0 else "N/A (Sem Produção)"
                    st.metric("⚖️ R$ / Proposição", roi_label, 
                              help="Custo médio por projeto de lei ou proposição legislativa.")

                st.divider()

                # ── Abas de visualização ──────────────────────────
                sub1, sub2, sub3, sub4, sub5, sub6 = st.tabs([
                    "💰 Despesas CEAP",
                    "🎙️ Discursos",
                    "📅 Eventos",
                    "🏛️ Órgãos",
                    "🏳️ Frentes",
                    "🧠 IA & Linguística",
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

                with sub6:
                    st.markdown("### 🧠 Inteligência Artificial (V4.0)")
                    ci1, ci2 = st.columns([1, 2])
                    
                    with ci1:
                        st.metric("📊 Índice de Complexidade", complexidade["score"], 
                                  help="Flesch Reading Ease (PT). Quanto maior, mais acessível o texto.")
                        st.markdown(f"**Nível de Acesso:**\n`{complexidade['nivel']}`")
                        
                        st.divider()
                        st.markdown("#### 🗣️ Sentimento & Retórica")
                        st.info(f"O tom predominante do discurso mais recente foi: **{sentimento}**")
                        
                        st.divider()
                        st.markdown("#### 📜 Resumo do Perfil (IA)")
                        st.success(resumo_ia)

                    with ci2:
                        st.markdown("#### 🔓 Tradutor de Politiquês")
                        if politiques != "N/A":
                            st.markdown(f"> **Último Projeto Simplicado:**\n> {politiques}")
                        else:
                            st.write("Nenhuma ementa recente para traduzir.")

                        st.markdown("#### ☁️ Nuvem de Temas Legislativos")
                        if tokens_deputado:
                            fig_wc = generate_wordcloud(tokens_deputado, titulo=f"Eixos de Atuação — {nome_oficial}")
                            if fig_wc:
                                st.pyplot(fig_wc)
                        else:
                            st.info("Nenhuma proposição registrada para gerar nuvem de temas.")

                # ── Seção de Auditoria (Novidade V2.0) ────────────
                st.divider()
                col_a1, col_a2 = st.columns([2, 1])
                with col_a1:
                    st.plotly_chart(plot_anomaly_bubbles(df_outliers), use_container_width=True)
                with col_a2:
                    if ceap_status:
                        st.plotly_chart(
                            plot_ceap_limit_gauge(ceap_status["total"], ceap_status["limite"], dados_dep.get("siglaUf", "??")),
                            use_container_width=True
                        )
                        if ceap_status["excedeu"]:
                            st.error(f"⚠️ **ALERTA**: O parlamentar excedeu o limite mensal da UF ({ceap_status['percentual']}% do teto).")
                        elif ceap_status["percentual"] > 80:
                            st.warning(f"🔔 **Atenção**: Gasto próximo ao limite mensal ({ceap_status['percentual']}%).")


    # ─── Aba 3: Rankings & Auditoria Global ────────────────────────
    with tab3:
        st.subheader("🏆 Rankings Globais e Auditoria da Casa")
        ano_sel_rank = st.selectbox("Escolha o ano para o ranking", options=anos_disponiveis, index=1)
        
        with st.spinner("Compilando dados de todos os 513 deputados..."):
            df_rank = get_ranking_gastos_global(ano_sel_rank)
        
        if df_rank.empty:
            st.info("Dados não disponíveis para este ano.")
        else:
            c1, c2, c3 = st.columns(3)
            total_casa = df_rank["total_gasto"].sum()
            c1.metric("💰 Total Gasto pela Câmara", f"R$ {total_casa/1e6:.1f}M")
            c2.metric("👤 Média por Deputado", f"R$ {(total_casa/513)/1e3:.1f}k")
            top_g = df_rank.iloc[0]["total_gasto"]
            c3.metric("📈 Maior Gasto Individual", f"R$ {top_g/1e3:.1f}k", help=f"Responsável: {df_rank.iloc[0]['nome']}")

            st.divider()
            col_r1, col_r2 = st.columns([2, 1])
            with col_r1:
                st.plotly_chart(plot_efficiency_quadrants(df_rank), use_container_width=True)
                st.plotly_chart(plot_spending_ranking(df_rank), use_container_width=True)
            with col_r2:
                st.markdown("### 🏆 Top 10 Eficiência (ROI)")
                # Ordenar por menor custo por proposição, mas apenas para quem tem ao menos 1 proposição
                df_roi = df_rank[df_rank["qtd_proposicoes"] > 0].sort_values("custo_por_proposicao", ascending=True).head(10)
                st.dataframe(
                    df_roi[["nome", "qtd_proposicoes", "custo_por_proposicao"]].style.format({
                        "custo_por_proposicao": lambda x: _fmt_brl(x).replace(",00", ""),
                        "qtd_proposicoes": "{:n}"
                    }),
                    hide_index=True,
                    use_container_width=True
                )
                
                st.divider()
                st.markdown("### 📋 Maiores Gastos")
                st.dataframe(
                    df_rank[["nome", "siglaPartido", "total_gasto"]].head(10).style.format({"total_gasto": "R$ {:,.2f}"}),
                    hide_index=True,
                    use_container_width=True
                )


    # ─── Aba 4: Sobre ───────────────────────────────────────────────
    with tab4:
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

def main_municipal():
    """Painel Legislativo da Câmara Municipal de Florianópolis."""
    tab1, tab2, tab3 = st.tabs([
        "👥 Servidores Públicos", 
        "📋 Pautas e Sessões", 
        "📺 TV Câmara & Notícias"
    ])
    
    with tab1:
        # ── Inicializa estado de navegação ────────────────────────
        if "vereador_sel" not in st.session_state:
            st.session_state.vereador_sel = None

        veredadores = loader_mun.get_vereadores()
        if not veredadores:
            st.warning("Não foi possível carregar a lista de servidores públicos.")
        else:
            COR_PARTIDO = {
                "PT": "#E53E3E", "PL": "#2B6CB0", "MDB": "#D69E2E",
                "PSD": "#2F855A", "PSOL": "#6B46C1", "PP": "#C05621",
                "REPUBLICANOS": "#B83280", "PDT": "#285E61", "PSDB": "#2563EB",
                "SOLIDARIEDADE": "#D97706", "UNIÃO": "#0F766E",
            }

            # ════════════════════════════════════════════════════════
            # MODO DETALHE: exibe perfil completo do vereador selecionado
            # ════════════════════════════════════════════════════════
            if st.session_state.vereador_sel is not None:
                v = st.session_state.vereador_sel
                nome    = v.get("nome") or v.get("nomeVereador") or "N/A"
                partido = (v.get("partido") or v.get("siglaPartido") or "—").upper()
                funcao  = v.get("funcao") or v.get("cargo") or "Vereador(a)"
                foto    = v.get("imagem") or v.get("urlFoto") or v.get("foto") or ""
                link    = v.get("link") or v.get("url") or ""
                cor     = COR_PARTIDO.get(partido, "#4A5568")

                # Botão de voltar
                if st.button("← Voltar à lista", key="btn_voltar_vereador"):
                    st.session_state.vereador_sel = None
                    st.rerun()

                st.divider()

                # ── Header do perfil ──────────────────────────────
                col_foto, col_info = st.columns([1, 3])
                with col_foto:
                    if foto:
                        st.markdown(
                            f"<img src='{foto}' style='width:160px;height:160px;border-radius:50%;"
                            f"object-fit:cover;border:4px solid {cor};display:block;margin:0 auto'>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"<div style='width:160px;height:160px;border-radius:50%;background:{cor};"
                            f"display:flex;align-items:center;justify-content:center;font-size:56px;"
                            f"margin:0 auto'>👤</div>",
                            unsafe_allow_html=True
                        )

                with col_info:
                    st.markdown(f"## {nome}")
                    st.markdown(
                        f"<span style='background:{cor};color:white;font-size:14px;font-weight:700;"
                        f"padding:4px 14px;border-radius:20px'>{partido}</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"**Cargo:** {funcao}")
                    st.markdown(f"**Câmara:** Câmara Municipal de Florianópolis (CMF-SC)")
                    if link:
                        st.link_button("🏛️ Ver perfil oficial na CMF", link)
                st.divider()

                # ── Proposições do servidor (busca por nome no pool real) ────
                st.markdown("### 📋 Proposições Legislativas")
                with st.spinner("Buscando proposições na base da CMF..."):
                    # Busca pool real de proposições (paginado por tipo)
                    todas_prop = loader_mun.get_proposicoes_lista()
                    # Filtro robusto: qualquer palavra significativa do nome
                    palavras_nome = [p for p in nome.lower().split() if len(p) > 3]
                    prop_rel = [
                        p for p in todas_prop
                        if any(w in str(p).lower() for w in palavras_nome)
                    ]

                if prop_rel:
                    for pr in prop_rel[:8]:
                        numero_pr = pr.get("numero") or pr.get("id") or ""
                        tipo_pr   = pr.get("tipo") or pr.get("descricaoTipo") or ""
                        ementa_pr = pr.get("ementa") or pr.get("titulo") or pr.get("descricao") or "Sem ementa"
                        data_pr   = pr.get("data") or pr.get("dataApresentacao") or ""
                        link_pr   = pr.get("link") or pr.get("url") or ""
                        linkify   = f" [🔗]({link_pr})" if link_pr else ""
                        st.markdown(f"📄 `{tipo_pr} {numero_pr}` `{data_pr}` — {ementa_pr}{linkify}")
                else:
                    # Se pool for vazio, provavelmente a API não retornou dados
                    if not todas_prop:
                        st.warning("⚠️ A API da CMF não retornou proposições na busca atual.")
                    else:
                        st.info(f"📋 Encontramos **{len(todas_prop)} proposições** na CMF, mas nenhuma com o nome '{nome}' no texto. Consulte o perfil oficial para a lista completa autoral.")

                # ── Notícias recentes com nome ─────────────────────────────────
                st.divider()
                st.markdown("### 📰 Notícias Recentes")
                with st.spinner("Varrendo notícias das últimas páginas..."):
                    # Busca mais páginas de notícias
                    noticias_all = loader_mun.get_noticias_todas()
                    palavras_nome = [p for p in nome.lower().split() if len(p) > 3]
                    noticias_rel = [
                        n for n in noticias_all
                        if any(w in str(n).lower() for w in palavras_nome)
                    ]

                if noticias_rel:
                    for n in noticias_rel[:6]:
                        data_n   = n.get("data") or ""
                        titulo_n = n.get("titulo") or n.get("descricao") or "Notícia"
                        link_n   = n.get("link") or n.get("url") or ""
                        linkify  = f" — [🔗 ler]({link_n})" if link_n else ""
                        st.markdown(f"📰 `{data_n}` {titulo_n}{linkify}")
                else:
                    if not noticias_all:
                        st.warning("⚠️ A API da CMF não retornou notícias nas últimas consultas.")
                    else:
                        st.info(f"📰 Varremos **{len(noticias_all)} notícias** da CMF. Nenhuma menciona '{nome.split()[0]}' diretamente. Consulte o portal oficial.")

            # ════════════════════════════════════════════════════════
            # MODO GRID: lista todos os vereadores em cards clicáveis
            # ════════════════════════════════════════════════════════
            else:
                st.subheader("Servidores Públicos de Florianópolis")
                st.metric("👥 Total de Servidores", len(veredadores))
                st.divider()

                cols = st.columns(4)
                for i, v in enumerate(veredadores):
                    nome    = v.get("nome") or v.get("nomeVereador") or "N/A"
                    partido = (v.get("partido") or v.get("siglaPartido") or "—").upper()
                    funcao  = v.get("funcao") or v.get("cargo") or "Vereador(a)"
                    foto    = v.get("imagem") or v.get("urlFoto") or v.get("foto") or ""
                    cor     = COR_PARTIDO.get(partido, "#4A5568")

                    with cols[i % 4]:
                        foto_html = (
                            f"<img src='{foto}' style='width:80px;height:80px;border-radius:50%;"
                            f"object-fit:cover;border:3px solid {cor};margin-bottom:8px;"
                            f"display:block;margin-left:auto;margin-right:auto'>"
                            if foto else
                            f"<div style='width:80px;height:80px;border-radius:50%;background:{cor};"
                            f"display:flex;align-items:center;justify-content:center;font-size:28px;"
                            f"margin:0 auto 8px auto'>👤</div>"
                        )
                        st.markdown(f"""
                        <div style='background:#1a1f2e;border:1px solid #2d3748;border-radius:12px;
                            padding:16px 12px;text-align:center;margin-bottom:4px'>
                            {foto_html}
                            <div style='font-weight:700;font-size:14px;color:#F7FAFC;
                                margin-bottom:4px;white-space:nowrap;overflow:hidden;
                                text-overflow:ellipsis' title='{nome}'>{nome}</div>
                            <span style='background:{cor};color:white;font-size:11px;
                                font-weight:700;padding:2px 8px;border-radius:20px;
                                display:inline-block;margin-bottom:4px'>{partido}</span>
                            <div style='color:#A0AEC0;font-size:12px'>{funcao}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Botão Streamlit sobreposto ao card
                        if st.button("👁️ Ver perfil", key=f"ver_{i}", use_container_width=True):
                            st.session_state.vereador_sel = v
                            st.rerun()

    with tab2:
        st.subheader("Pautas das Próximas Sessões")
        pautas = loader_mun.get_pautas()
        if not pautas:
            st.info("Nenhuma pauta recente encontrada.")
        else:
            # Dicionário de Comissões da CMF-Florianópolis
            COMISSOES_CMF = {
                "CCJ":      ("Constituição e Justiça",                       "Analisa a constitucionalidade e legalidade de propostas de lei."),
                "CECD":     ("Educação, Cultura e Desporto",                   "Discute ensino, projetos culturais e programas esportivos no município."),
                "CDDPD":    ("Direitos das Pessoas com Deficiência",           "Analisa políticas de acessibilidade, inclusão e direitos de PcD."),
                "CDDMPIG":  ("Direitos das Mulheres e Inclusão de Gênero",    "Pauta políticas para igualdade de gênero e proteção à mulher."),
                "CTLSSP":   ("Turismo, Lazer, Segurança e Serviço Público",  "Debute turismo sustentável, segurança pública e serviços ao cidadão."),
                "CCTOII":   ("Ciência, Tecnologia, Obras e Infraestrutura",   "Pauta inovação, obras públicas e desenvolvimento de infraestrutura."),
                "CVOPU":    ("Vigilância, Obras Públicas e Urbanismo",        "Fiscaliza obras públicas e discute planejamento urbano da cidade."),
                "CS":       ("Saúde",                                          "Debate saúde pública: UBSs, hospitais, vigilância sanitária."),
                "CF":       ("Finanças",                                       "Analisa o orçamento municipal, tributos e contas públicas."),
                "CMMA":     ("Meio Ambiente",                                   "Discusses preservação ambiental, saneamento e fauna urbana."),
                "CMH":      ("Habitação",                                      "Analisa projetos de moradia, regularização fundiária e PMCMV."),
                "CTA":      ("Transporte e Acessibilidade",                    "Debate mobilidade urbana, transporte coletivo e ciclovias."),
            }
            TIPO_SESSAO = {
                "Audiência Pública":             ("🎙️", "Sessão aberta à participação cidadã. Qualquer pessoa pode se inscrever para falar."),
                "Sessão Ordinária":              ("🏗️", "Sessão regular do plenário para votação de projetos de lei e deliberações."),
                "Sessão Extraordinária":         ("⚡", "Convocada fora do calendário regular para pautas urgentes."),
                "Reunião Ordinária de Comissão": ("📋", "Reunião técnica de comissão para análise detalhada de propostas."),
                "Reunião Extraordinária de Comissão": ("⚡📋", "Reunião de comissão fora do calendário por urgência."),
            }

            import re as _re

            def _resumo_pauta(titulo: str) -> tuple:
                icone, tipo_desc = "📋", ""
                for tipo, (ico, desc) in TIPO_SESSAO.items():
                    if tipo.lower() in titulo.lower():
                        icone, tipo_desc = ico, desc
                        break
                match = _re.search(r'\(([A-Z]{2,10})\)', titulo)
                comissao_txt = ""
                if match:
                    sigla = match.group(1)
                    if sigla in COMISSOES_CMF:
                        nome, desc_c = COMISSOES_CMF[sigla]
                        comissao_txt = f"**Comissão:** {nome} `({sigla})`  —  {desc_c}"
                    else:
                        comissao_txt = f"**Comissão:** `{sigla}`"
                resumo = comissao_txt
                if tipo_desc:
                    resumo += ("\n\n" if comissao_txt else "") + f"_{tipo_desc}_"
                return icone, resumo or "🏗️ Sessão legislativa da Câmara Municipal de Florianópolis."

            for p in pautas[:15]:
                data_fmt = p.get("data") or p.get("dataSessao") or "Data não informada"
                titulo = p.get("titulo") or p.get("nome") or "Sem Título"
                link = p.get("url") or p.get("link") or p.get("urlPauta") or ""
                icone, resumo = _resumo_pauta(titulo)
                with st.expander(f"{icone} {data_fmt} — {titulo}"):
                    st.markdown(resumo)
                    if link:
                        st.markdown(f"[📄 Ver proposições em pauta]({link})")

    with tab3:
        st.subheader("Últimas Notícias e Vídeos")
        noticias = loader_mun.get_noticias()
        tv = loader_mun.get_tv_camara()
        
        col_n, col_v = st.columns(2)
        with col_n:
            st.markdown("#### 📰 Portal de Notícias (CMF)")
            for n in noticias[:5]:
                st.markdown(f"**{n.get('data')}** - {n.get('titulo')}")
                st.caption(n.get("resumo", ""))
                st.divider()
        
        with col_v:
            st.markdown("#### 🎥 TV Câmara Florianópolis")
            if not tv:
                st.info("Nenhum vídeo disponível no momento.")
            else:
                for video in tv[:5]:
                    titulo = video.get("titulo") or video.get("descricao") or "Vídeo CMF"
                    legenda = video.get("data") or video.get("dataSessao") or ""
                    
                    # A CMF pode usar campos variados para a URL
                    link = (
                        video.get("url") or video.get("urlVideo") or
                        video.get("link") or video.get("urlYoutube") or ""
                    )
                    
                    # Tenta embed do YouTube se for link YT
                    if link and ("youtube.com" in link or "youtu.be" in link):
                        try:
                            st.video(link)
                            st.caption(f"📅 {legenda} — {titulo}")
                        except Exception:
                            st.markdown(f"🎬 [{titulo}]({link})")
                    elif link:
                        # Link de página HTML → exibe como card clicável
                        st.markdown(
                            f"""<div style='border:1px solid #374151; border-radius:8px;
                                padding:12px; margin-bottom:8px; background:#111827'>
                            🎬 <a href="{link}" target="_blank" style='color:#60A5FA;
                                text-decoration:none; font-weight:600'>{titulo}</a>
                            <br><small style='color:#9CA3AF'>📅 {legenda}</small>
                            </div>""",
                            unsafe_allow_html=True
                        )
                    else:
                        # Sem URL — mostra o que tiver
                        with st.expander(f"🎬 {titulo}"):
                            st.json(video)

# ── Execução do App ───────────────────────────────────────────
if escopo == "🇧🇷 Federal (Brasília)":
    main_federal()
else:
    main_municipal()
