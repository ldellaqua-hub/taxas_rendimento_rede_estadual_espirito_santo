import streamlit as st
import pandas as pd

st.set_page_config(page_title="Painel de Rendimento - ES", layout="wide")

# ====== Cabeçalho ======
st.title("Painel de Taxas de Rendimento – Rede Estadual/ES (por Município)")
st.caption("por **Luciene Dellaqua Bergamin** • Fonte: INEP (Censo Escolar/Situação do Aluno)")

# ====== Navegação ======
sec = st.sidebar.radio(
    "Seções",
    ["Início", "Visão Geral – ES", "Ranking de Municípios", "Evolução Temporal", "Comparador", "Metodologia & Fontes"]
)
