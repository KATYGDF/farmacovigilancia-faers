"""Painel de Farmacovigilância — Dashboard Streamlit (4 abas).

Integra os 3 pilares do projeto:
- Visão Geral (KPIs + top drugs/reactions)
- Sinais (disproporcionalidade PRR/ROR/IC)
- Severidade (XGBoost + SHAP)
- Rede (grafo droga-droga + comunidades)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import joblib
import matplotlib as mpl
import matplotlib.pyplot as plt

# Evita ValueError do mathtext quando nomes de features têm $/^/_/{} (ex.: feature names do ColumnTransformer)
mpl.rcParams["text.parse_math"] = False

import networkx as nx
import numpy as np
import pandas as pd
import shap
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

from app.ui.estilos_css import aplicar_estilos_css

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Farmacovigilância FAERS 2023",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)
aplicar_estilos_css()

DASH = ROOT / "data" / "processed" / "dashboard"
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"


# ---------------------------------------------------------------------------
# Carregamento com cache
# ---------------------------------------------------------------------------
@st.cache_data
def load_summary() -> dict:
    return json.loads((DASH / "summary.json").read_text())


@st.cache_data
def load_top_drugs() -> pd.DataFrame:
    return pd.read_parquet(DASH / "top_drugs.parquet")


@st.cache_data
def load_top_reactions() -> pd.DataFrame:
    return pd.read_parquet(DASH / "top_reactions.parquet")


@st.cache_data
def load_outcomes() -> pd.DataFrame:
    return pd.read_parquet(DASH / "outcomes.parquet")


@st.cache_data
def load_model_lists() -> dict:
    return json.loads((DASH / "model_lists.json").read_text())


@st.cache_data
def load_signals() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "signals_2023.parquet")


@st.cache_data
def load_network_edges() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "network_edges_2023.parquet")


@st.cache_data
def load_network_centrality() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "network_centrality_2023.parquet")


@st.cache_resource
def load_severity_model():
    return (
        joblib.load(MODELS / "xgb_severity.pkl"),
        joblib.load(MODELS / "preprocessor_severity.pkl"),
    )


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="main-header">
      <h1>💊 Farmacovigilância FAERS 2023</h1>
      <p>Detecção de sinais de segurança · Predição de severidade · Análise de rede de drogas</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Visão Geral",
    "🚨 Sinais de Segurança",
    "⚕️ Predição de Severidade",
    "🕸️ Rede Droga-Droga",
])

# ===========================================================================
# Aba 1 — Visão Geral
# ===========================================================================
with tab1:
    summary = load_summary()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-value">{summary['total_cases']/1e6:.2f}M</div>
              <div class="metric-label">Casos únicos (após dedup)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-value">{summary['serious_rate_pct']:.1f}%</div>
              <div class="metric-label">Taxa de desfecho sério</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-value">{summary['death_rate_pct']:.1f}%</div>
              <div class="metric-label">Taxa de óbito</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-value">{summary['total_unique_drugs']/1000:.0f}k</div>
              <div class="metric-label">Drogas únicas reportadas</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("### 💊 Top 20 medicamentos (suspeito primário)")
        td = load_top_drugs().head(20)
        st.bar_chart(td.set_index("drug")["count"], horizontal=True, color="#1F5082")

    with col_r:
        st.markdown("### ⚠️ Top 20 reações reportadas")
        tr = load_top_reactions().head(20)
        st.bar_chart(tr.set_index("reaction")["count"], horizontal=True, color="#1F5082")

    st.markdown("---")
    st.markdown("### 🏥 Distribuição de desfechos")
    outcomes = load_outcomes()
    st.bar_chart(outcomes.set_index("label")["count"], color="#1F5082")

    st.caption(
        f"Período: {summary['year']} ({summary['n_quarters']} trimestres) · "
        f"Fonte: FAERS (FDA) · "
        f"Casos com desfecho: {summary['cases_with_outcome']:,}"
    )


# ===========================================================================
# Aba 2 — Sinais
# ===========================================================================
with tab2:
    st.markdown("### 🚨 Sinais de Segurança por Disproporcionalidade")
    st.info(
        "🔬 Buscamos pares **droga × reação** que ocorrem com frequência maior que o esperado, "
        "usando PRR (Proportional Reporting Ratio), ROR (Reporting Odds Ratio) e IC (Information Component) "
        "com intervalo de confiança 95%."
    )

    signals = load_signals()
    drugs_available = sorted(signals["drug"].value_counts().head(500).index.tolist())

    drug_sel = st.selectbox(
        "🔍 Escolha um medicamento para investigar",
        options=drugs_available,
        index=drugs_available.index("WARFARIN") if "WARFARIN" in drugs_available else 0,
    )

    sub = signals[signals["drug"] == drug_sel].copy()
    sub = sub.sort_values("ic", ascending=False)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Reações reportadas", f"{len(sub):,}")
    with col2:
        st.metric("Sinais positivos (qualquer)", f"{int(sub['any_signal'].sum()):,}")
    with col3:
        st.metric("Sinais fortes (IC025 > 0)", f"{int(sub['ic_signal'].sum()):,}")

    st.markdown(f"#### Top 30 reações para **{drug_sel}** (ordenadas por IC)")

    display = sub.head(30)[[
        "reaction", "a", "prr", "prr_ci_low", "prr_ci_high",
        "ror", "ic", "ic_ci_low", "any_signal"
    ]].copy()
    display.columns = [
        "Reação", "N relatos", "PRR", "PRR ic95↓", "PRR ic95↑",
        "ROR", "IC", "IC ic95↓", "Sinal?"
    ]
    display = display.round(2)
    display["Sinal?"] = display["Sinal?"].map({True: "🔴", False: "—"})

    st.dataframe(display, use_container_width=True, hide_index=True, height=600)

    st.caption(
        "💡 **Como interpretar:** PRR ≥ 2 com χ² ≥ 4 e a ≥ 3 indica sinal positivo (FDA). "
        "IC com limite inferior > 0 é o critério mais conservador (UMC/Uppsala). "
        "Sinais ≠ causalidade — apenas associação."
    )


# ===========================================================================
# Aba 3 — Severidade
# ===========================================================================
with tab3:
    st.markdown("### ⚕️ Predição de severidade do evento")
    st.info(
        "🎯 Dado o perfil do paciente e a droga reportada, qual a probabilidade de o desfecho ser **sério** "
        "(morte, hospitalização, risco de vida, incapacidade)?"
    )

    model, preprocessor = load_severity_model()
    lists = load_model_lists()

    col_input, col_output = st.columns([1, 2])

    with col_input:
        st.markdown("#### 👤 Dados do caso")
        with st.form("severity_form"):
            age = st.slider("Idade (anos)", 0, 100, 60)
            sex = st.selectbox("Sexo", lists["sex"], index=0)
            drug_name = st.selectbox(
                "💊 Medicamento principal",
                lists["primary_drug"],
                index=lists["primary_drug"].index("WARFARIN") if "WARFARIN" in lists["primary_drug"] else 0,
            )
            indication = st.selectbox(
                "🩺 Indicação clínica",
                lists["primary_indication"],
                index=lists["primary_indication"].index("UNKNOWN") if "UNKNOWN" in lists["primary_indication"] else 0,
            )
            n_drugs_total = st.slider("Nº total de medicamentos", 1, 30, 4)
            n_drugs_concomitant = st.slider("Nº de drogas concomitantes", 0, 25, 2)
            n_indications = st.slider("Nº de indicações", 0, 10, 1)
            reporter = st.selectbox("Tipo de reportante", lists["reporter_type"], index=0)
            submitted = st.form_submit_button("🔬 Calcular risco", type="primary", use_container_width=True)

    with col_output:
        if submitted or True:  # auto-update no primeiro load
            row = pd.DataFrame([{
                "age_years": age,
                "n_drugs_total": n_drugs_total,
                "n_drugs_ps": 1,
                "n_drugs_concomitant": n_drugs_concomitant,
                "n_indications": n_indications,
                "sex": sex,
                "primary_drug": drug_name,
                "primary_indication": indication,
                "reporter_type": reporter,
            }])

            X = preprocessor.transform(row)
            prob = float(model.predict_proba(X)[0, 1])

            if prob < 0.35:
                grad = "linear-gradient(135deg, #10B981 0%, #047857 100%)"
                label = "Baixo"
            elif prob < 0.6:
                grad = "linear-gradient(135deg, #F59E0B 0%, #B45309 100%)"
                label = "Moderado"
            else:
                grad = "linear-gradient(135deg, #EF4444 0%, #B91C1C 100%)"
                label = "Alto"

            st.markdown(
                f"""
                <div class="metric-card" style="background:{grad};">
                  <div class="metric-label" style="font-size:0.95rem;">Probabilidade de desfecho sério</div>
                  <div class="metric-value" style="font-size:3.2rem;">{prob*100:.1f}%</div>
                  <div class="metric-label" style="font-size:1.05rem;">Risco: <b>{label}</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(
                "Taxa média populacional: **49,3%**. Modelo XGBoost tunado (ROC-AUC test: 0,74)."
            )

            # SHAP local — implementação custom para evitar bug do shap.plots.waterfall em Streamlit
            st.markdown("#### 🔍 Por que esse risco?")
            explainer = shap.TreeExplainer(model)
            feature_names = preprocessor.get_feature_names_out()
            shap_vals = explainer.shap_values(X)[0]
            base_value = float(explainer.expected_value)

            contribs = (
                pd.DataFrame({
                    "feature": [f.replace("num__", "").replace("cat__", "") for f in feature_names],
                    "shap": shap_vals,
                    "value": X[0],
                })
                .assign(abs_shap=lambda d: d["shap"].abs())
                .sort_values("abs_shap", ascending=False)
                .head(10)
                .sort_values("shap")
            )

            fig, ax = plt.subplots(figsize=(9, 5))
            colors = ["#EF4444" if v > 0 else "#1F5082" for v in contribs["shap"]]
            labels = [f"{f}  =  {v:.2f}" if isinstance(v, (int, float)) and not np.isnan(v) else f
                      for f, v in zip(contribs["feature"], contribs["value"])]
            ax.barh(labels, contribs["shap"], color=colors, edgecolor="white", linewidth=0.5)
            ax.axvline(0, color="#0F172A", linewidth=0.8)
            ax.set_xlabel("Impacto SHAP (↑ aumenta risco · ↓ reduz risco)", fontsize=10)
            pred_logit = base_value + shap_vals.sum()
            ax.set_title(
                f"Base value: {base_value:.3f}  →  Predicted (logit): {pred_logit:.3f}",
                fontsize=10, color="#334155",
            )
            ax.spines[["top", "right"]].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)


# ===========================================================================
# Aba 4 — Rede
# ===========================================================================
with tab4:
    st.markdown("### 🕸️ Rede de co-reporte droga-droga")
    st.info(
        "🔗 Nós = medicamentos · Arestas = co-reporte no mesmo caso · Cores = comunidades (Louvain). "
        "Drogas conectadas tendem a ser **prescritas juntas** — comunidades refletem classes terapêuticas."
    )

    edges = load_network_edges()
    central = load_network_centrality()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nós (drogas)", f"{central['drug'].nunique():,}")
    with col2:
        st.metric("Arestas (co-reportes)", f"{len(edges):,}")
    with col3:
        st.metric("Comunidades", f"{int(central['community'].nunique())}")

    n_show = st.slider("Mostrar top-N nós mais centrais", 30, 200, 80, step=10)

    # Filtrar para top-N
    top_drugs_set = set(central.nlargest(n_show, "eigenvector")["drug"])
    edges_sub = edges[edges["source"].isin(top_drugs_set) & edges["target"].isin(top_drugs_set)]

    # Pré-calcular posições com NetworkX (estável, deterministica via seed)
    sub_g = nx.from_pandas_edgelist(edges_sub, "source", "target", edge_attr="weight")
    for d in top_drugs_set:
        sub_g.add_node(d)
    pos = nx.spring_layout(sub_g, k=1.5, iterations=200, seed=42, weight="weight")

    # PyVis com física DESLIGADA — usa as posições calculadas
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="#0F172A", notebook=False)
    comm_colors = ["#1F5082", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4",
                   "#F472B6", "#84CC16", "#FB923C", "#22D3EE"]

    drug_to_comm = dict(zip(central["drug"], central["community"]))
    drug_to_eigen = dict(zip(central["drug"], central["eigenvector"]))

    # Escala para o canvas (PyVis trabalha em pixels)
    SCALE = 800

    for d in top_drugs_set:
        c = drug_to_comm.get(d, 0)
        color = comm_colors[c % len(comm_colors)]
        size = 12 + 60 * drug_to_eigen.get(d, 0)
        x, y = pos[d]
        net.add_node(
            d, label=d, color=color, size=size,
            title=f"{d}<br>Comunidade {c}",
            x=float(x) * SCALE, y=float(y) * SCALE,
            physics=False,  # nó fixo
        )

    for _, e in edges_sub.iterrows():
        net.add_edge(e["source"], e["target"], value=float(e["weight"]),
                     color="rgba(180,180,180,0.35)")

    # Desliga toda física + configura interação
    net.set_options("""
    {
      "physics": {"enabled": false},
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "zoomView": true,
        "dragView": true,
        "dragNodes": true
      },
      "nodes": {"borderWidth": 1},
      "edges": {"smooth": false}
    }
    """)
    html = net.generate_html(notebook=False)
    components.html(html, height=620, scrolling=False)

    with st.expander("ℹ️ Como interagir e interpretar o grafo"):
        st.markdown(
            """
            **🖱️ Interação:**
            - **Arrastar fundo** — mover toda a vista
            - **Scroll do mouse** — zoom in/out
            - **Arrastar um nó** — reposicionar manualmente uma droga
            - **Passar o cursor sobre um nó** — ver nome + comunidade
            - Aguarde alguns segundos no primeiro carregamento — os nós se ajustam até pararem

            **🎨 Como ler o grafo:**
            - **Tamanho do nó** = centralidade eigenvector (drogas grandes são *hubs* — aparecem com muitas outras)
            - **Cor do nó** = comunidade Louvain (drogas da mesma cor são prescritas juntas)
            - **Espessura da aresta** = nº de casos em que as duas drogas foram co-reportadas
            - **Distância** = drogas próximas tendem a aparecer em casos similares

            **🧠 O que procurar:**
            - **Hubs grandes no centro** — analgésicos comuns, vitaminas, AAS (polifarmácia geriátrica)
            - **Aglomerados coloridos** — refletem classes terapêuticas reais (oncológicos, reumatológicos, opioides)
            - **Nós periféricos** — drogas mais isoladas, pouco co-prescritas
            """
        )

    st.markdown("#### 🏆 Top 15 drogas mais centrais (eigenvector)")
    top_cent = central.head(15)[["drug", "degree_w", "eigenvector", "community"]].round(4)
    top_cent.columns = ["Droga", "Grau ponderado", "Eigenvector", "Comunidade"]
    st.dataframe(top_cent, use_container_width=True, hide_index=True)
