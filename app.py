import streamlit as st

from views import action_plan, assessment, dashboard, history, home

st.set_page_config(
    page_title="ISO/IEC 27002:2022 — Conformidade",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """<style>
    .stButton > button { border-radius: 8px; font-weight: 500; }
    .stProgress > div > div > div { background-color: #1d4ed8; }
    </style>""",
    unsafe_allow_html=True,
)

if "page" not in st.session_state:
    st.session_state.page = "home"
if "avaliacoes" not in st.session_state:
    st.session_state.avaliacoes = {}
if "historico" not in st.session_state:
    st.session_state.historico = []

ROTAS = {
    "home": home.render,
    "assessment": assessment.render,
    "dashboard": dashboard.render,
    "action_plan": action_plan.render,
    "history": history.render,
}
ROTAS.get(st.session_state.page, home.render)()
