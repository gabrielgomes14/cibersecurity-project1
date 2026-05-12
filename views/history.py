import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.controls import TEMA_LABELS, TEMAS


def _safe_float(v: object) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v))
    except (TypeError, ValueError):
        return 0.0


def _render_grafico_tendencia(historico: list[dict[str, object]]) -> None:
    if not historico:
        return
    fig = go.Figure()
    rotulos = [str(s.get("rotulo", "")) for s in historico]
    geral = [_safe_float(s.get("score_geral")) for s in historico]
    fig.add_trace(go.Scatter(x=rotulos, y=geral, mode="lines+markers", name="Geral", line={"color": "#1d4ed8", "width": 3}))
    for tema_id, tema_label in TEMA_LABELS.items():
        valores: list[float] = []
        for s in historico:
            sct = s.get("scores_por_tema", {})
            if isinstance(sct, dict):
                valores.append(_safe_float(sct.get(tema_id)))
            else:
                valores.append(0.0)
        fig.add_trace(go.Scatter(x=rotulos, y=valores, mode="lines+markers", name=tema_label, opacity=0.6))
    fig.update_layout(
        yaxis={"range": [0, 100], "title": "Score"},
        height=420,
        margin={"t": 20, "b": 30, "l": 40, "r": 20},
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.25},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def render() -> None:
    st.title("📈 Histórico de Avaliações")
    historico: list[dict[str, object]] = st.session_state.historico

    if not historico:
        st.info("Nenhum snapshot salvo ainda. Vá para o resultado da avaliação e clique em **Salvar snapshot no histórico**.")
        if st.button("Ir para Avaliação"):
            st.session_state.page = "assessment"
            st.rerun()
        return

    st.caption(f"{len(historico)} snapshot(s) registrado(s).")
    _render_grafico_tendencia(historico)

    st.divider()
    st.subheader("Tabela de snapshots")
    def _scores_dict(s: dict[str, object]) -> dict[str, float]:
        raw = s.get("scores_por_tema", {})
        if isinstance(raw, dict):
            return {str(k): _safe_float(v) for k, v in raw.items()}
        return {}

    df = pd.DataFrame([
        {
            "Rótulo": s.get("rotulo", ""),
            "Quando": s.get("timestamp", ""),
            "Avaliados": s.get("avaliados", 0),
            "Score Geral": round(_safe_float(s.get("score_geral")), 1),
            **{TEMA_LABELS[t]: round(_scores_dict(s).get(t, 0.0), 1) for t in TEMAS},
        }
        for s in historico
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    col_l, col_v = st.columns([3, 1])
    with col_l:
        rotulos = [str(s.get("rotulo", "")) for s in historico]
        remover = st.selectbox("Selecionar snapshot para remover", options=[""] + rotulos)
    with col_v:
        if st.button("Remover", use_container_width=True, disabled=not remover):
            st.session_state.historico = [s for s in historico if s.get("rotulo") != remover]
            st.rerun()

    with st.sidebar:
        st.markdown("### Navegação")
        if st.button("🏠 Início", use_container_width=True, key="hist_home"):
            st.session_state.page = "home"
            st.rerun()
        if st.button("📋 Avaliação", use_container_width=True, key="hist_assess"):
            st.session_state.page = "assessment"
            st.rerun()
        if st.button("📊 Resultado", use_container_width=True, key="hist_dash"):
            st.session_state.page = "dashboard"
            st.rerun()
