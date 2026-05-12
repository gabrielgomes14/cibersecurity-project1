import pandas as pd
import streamlit as st

from components.score_gauge import render_bar_temas, render_gauge, render_radar
from components.theme_summary import render_theme_summary
from data.controls import TEMA_LABELS, TEMAS, TODOS_CONTROLES
from logic.action_plan import gerar_plano
from logic.export import gerar_csv, montar_linhas
from logic.history import criar_snapshot, snapshot_para_dict
from logic.models import Avaliacao
from logic.pdf_report import gerar_pdf
from logic.scoring import resumo_tema, score_geral, status_label


def render() -> None:
    st.title("📊 Resultado da Avaliação")
    avaliacoes: dict[str, Avaliacao] = st.session_state.avaliacoes

    ponderado = st.toggle(
        "Pontuação ponderada por criticidade",
        value=st.session_state.get("ponderado", True),
        key="ponderado",
        help="Quando ativo, controles 'Alta' pesam 3x e 'Baixa' 1x.",
    )

    todos_ids = [c.id for c in TODOS_CONTROLES]
    score_total = score_geral(avaliacoes, todos_ids, ponderado=ponderado)
    resumos = {
        tema_id: resumo_tema(avaliacoes, tema_id, [c.id for c in controles], ponderado=ponderado)
        for tema_id, controles in TEMAS.items()
    }

    col1, col2 = st.columns([1, 2])
    with col1:
        render_gauge(score_total, "Score Geral")
        st.markdown(f"**Classificação:** {status_label(score_total)}")
    with col2:
        labels = [TEMA_LABELS[t] for t in TEMAS]
        scores = [resumos[t].score for t in TEMAS]
        render_radar(labels, scores)

    st.divider()
    st.subheader("Resumo por tema")
    cols = st.columns(len(TEMAS))
    for col, tema_id in zip(cols, TEMAS, strict=True):
        with col:
            r = resumos[tema_id]
            render_theme_summary(TEMA_LABELS[tema_id], r.score, r.conformes, r.total)

    st.divider()
    st.subheader("Comparativo entre temas")
    render_bar_temas(
        [TEMA_LABELS[t] for t in TEMAS],
        [resumos[t].score for t in TEMAS],
    )

    st.divider()
    st.subheader("Detalhamento por controle")
    linhas = montar_linhas(TODOS_CONTROLES, avaliacoes)
    df = pd.DataFrame([
        {
            "Controle": linha.controle_id,
            "Tema": linha.tema,
            "Título": linha.titulo,
            "Status": linha.status,
            "Criticidade": linha.criticidade,
            "Responsável": linha.responsavel,
            "Prazo": linha.prazo,
        }
        for linha in linhas
    ])
    temas_filtro = st.multiselect("Filtrar por tema", sorted(df["Tema"].unique()), default=list(df["Tema"].unique()))
    status_filtro = st.multiselect("Filtrar por status", sorted(df["Status"].unique()), default=list(df["Status"].unique()))
    df_filtrado = df[df["Tema"].isin(temas_filtro) & df["Status"].isin(status_filtro)]
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📥 Exportar")
    organizacao = st.text_input("Nome da organização (para o relatório)", value=st.session_state.get("organizacao", "Organização"), key="organizacao")
    acoes = gerar_plano(TODOS_CONTROLES, avaliacoes)

    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        st.download_button(
            "⬇️ CSV detalhado",
            data=gerar_csv(TODOS_CONTROLES, avaliacoes),
            file_name="relatorio_iso27002.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_d2:
        st.download_button(
            "📄 PDF executivo",
            data=gerar_pdf(TODOS_CONTROLES, avaliacoes, acoes, organizacao=organizacao, ponderado=ponderado),
            file_name="relatorio_iso27002.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with col_d3:
        rotulo = st.text_input("Rótulo do snapshot", value="", placeholder="Ex.: 2026 T2 baseline", key="rotulo_snapshot", label_visibility="collapsed")
        if st.button("📈 Salvar snapshot no histórico", use_container_width=True):
            snap = criar_snapshot(avaliacoes, rotulo=rotulo)
            st.session_state.historico.append(snapshot_para_dict(snap))
            st.toast("Snapshot adicionado ao histórico.", icon="📈")

    with st.sidebar:
        st.markdown("### Navegação")
        if st.button("🏠 Início", use_container_width=True, key="nav_home"):
            st.session_state.page = "home"
            st.rerun()
        if st.button("← Voltar à avaliação", use_container_width=True, key="nav_assess"):
            st.session_state.page = "assessment"
            st.rerun()
        if st.button("📌 Plano de ação", use_container_width=True, key="nav_action"):
            st.session_state.page = "action_plan"
            st.rerun()
        if st.button("📈 Histórico", use_container_width=True, key="nav_hist"):
            st.session_state.page = "history"
            st.rerun()
