from typing import Any

import streamlit as st

from data.controls import TEMA_LABELS, TEMAS, TODOS_CONTROLES
from logic.models import Avaliacao
from logic.persistence import deserializar, serializar


def _load_uploaded(arquivo: Any) -> None:
    try:
        avaliacoes, historico = deserializar(arquivo.read())
    except Exception as exc:
        st.error(f"Não foi possível ler o arquivo: {exc}")
        return
    st.session_state.avaliacoes = avaliacoes
    st.session_state.historico = historico
    st.toast(f"Importado: {len(avaliacoes)} avaliações, {len(historico)} snapshots.", icon="✅")


def render() -> None:
    st.title("🛡️ Diagnóstico de Conformidade — ISO/IEC 27002:2022")
    st.markdown(
        "Avalie o nível de aderência da sua organização aos **93 controles** "
        "da norma ISO/IEC 27002:2022, organizados em quatro temas."
    )
    st.divider()

    st.subheader("Temas avaliados")
    cols = st.columns(4)
    icones = {"org": "🏛️", "people": "👥", "physical": "🏢", "tech": "💻"}
    for col, (tema_id, controles) in zip(cols, TEMAS.items(), strict=True):
        with col, st.container(border=True):
            st.markdown(f"### {icones[tema_id]} {TEMA_LABELS[tema_id]}")
            st.metric("Controles", len(controles))

    st.divider()
    avaliacoes: dict[str, Avaliacao] = st.session_state.avaliacoes
    avaliados = sum(1 for a in avaliacoes.values() if a.status)
    if avaliados:
        st.success(f"Você já avaliou **{avaliados}** de {len(TODOS_CONTROLES)} controles. Continue de onde parou.")
    else:
        st.info(f"Total de **{len(TODOS_CONTROLES)}** controles a serem avaliados.")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        if st.button("📋 Iniciar / Continuar Avaliação", type="primary", use_container_width=True):
            st.session_state.page = "assessment"
            st.rerun()
    with col_b:
        if st.button("📈 Ver Histórico", use_container_width=True, disabled=not st.session_state.historico):
            st.session_state.page = "history"
            st.rerun()

    st.divider()
    st.subheader("📂 Importar / Exportar")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown("**Exportar avaliação atual**")
        st.download_button(
            "⬇️ Baixar JSON",
            data=serializar(avaliacoes, st.session_state.historico),
            file_name="diagnostico_iso27002.json",
            mime="application/json",
            disabled=not avaliacoes,
            use_container_width=True,
        )
    with col_e2:
        st.markdown("**Importar avaliação salva**")
        arquivo = st.file_uploader(
            "Selecionar JSON",
            type=["json"],
            label_visibility="collapsed",
            key="upload_json",
        )
        if arquivo is not None:
            _load_uploaded(arquivo)
