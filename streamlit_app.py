import streamlit as st


# Configuração da página
st.set_page_config(
page_title="Início",
page_icon="📊",
layout="wide"
)


# Título e descrição
st.title("📊 Painel de Taxas de Rendimento – Rede Estadual/ES (por Município)")


st.markdown("""
Esta aplicação apresenta um MVP (Produto Mínimo Viável) como parte da avaliação da disciplina de Cloud Computing
para produtos de dados na Pós-graduação em Mineração de Dados.


- Professor: Maxwell Monteiro
- Aluna: Luciene Dellaqua Bergamin
""")


st.subheader("Objetivo do Projeto")
st.write("""
O objetivo é criar um painel interativo para visualização e análise das **taxas de rendimento escolar** da rede estadual do Espírito Santo,
disponibilizadas por município. A aplicação servirá de base para futuras expansões, permitindo a incorporação de gráficos, comparações
e análises detalhadas dos dados educacionais.
""")


st.subheader("Fonte dos Dados")
st.write("""
Os dados utilizados neste projeto são públicos e foram obtidos através do portal de microdados do
Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP). Foram utilizados
principalmente os dados do **Censo Escolar**, em especial o módulo Situação do Aluno, que subsidia
o cálculo das taxas de Aprovação, Reprovação e Abandono.
""")


st.info("Navegue pelas seções no menu à esquerda para explorar os dados.")


# ====== Navegação ======
sec = st.sidebar.radio(
    "Seções",
    ["Início", "Visão Geral – ES", "Ranking de Municípios", "Evolução Temporal", "Comparador", "Metodologia & Fontes"]
)

