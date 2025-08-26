import streamlit as st

# =============================
# CONFIGURAÇÃO DA PÁGINA
# =============================
st.set_page_config(
    page_title="Início — Painel IDEB",
    page_icon="📈",
    layout="wide",
)

# =============================
# CABEÇALHO / APRESENTAÇÃO (APENAS TEXTO)
# =============================
st.title("📈 Painel IDEB – Rede Estadual/ES (por Município)")

st.markdown(
    """
    Esta aplicação apresenta um MVP (Produto Mínimo Viável) como parte da avaliação da disciplina de **Cloud Computing**
    para produtos de dados na Pós‑graduação em **Mineração de Dados**.

    - Professor: **Maxwell Monteiro**  
    - Aluna: **Luciene Dellaqua Bergamin**
    """
)

st.subheader("Objetivo do Projeto")
st.write(
    """
    Criar um painel de apresentação para exploração do **IDEB (Índice de Desenvolvimento da Educação Básica)** da rede 
    estadual do Espírito Santo, com foco em visualizações e comparações **por município**. Este MVP não carrega dados
    reais — serve como base de estrutura para, futuramente, incluir upload de CSV, gráficos e painéis analíticos.
    """
)

st.subheader("O que é o IDEB (resumo)")
st.write(
    """
    O IDEB combina **aprendizado** (proficiência medida pelo **Saeb**) e **fluxo escolar** (principalmente a **taxa de aprovação**
    do Censo Escolar). De forma simplificada, o indicador reflete quanto os estudantes **aprendem** e **progridem** ao longo do tempo.
    É divulgado bianualmente e pode ser analisado por **rede**, **município** e **escola**.
    """
)

st.subheader("Fontes dos Dados (apenas IDEB e Censo Escolar)")
st.write(
    """
    - **INEP / Saeb** – Proficiências em Língua Portuguesa e Matemática utilizadas na composição do **IDEB**.  
    - **INEP / Censo Escolar (Situação do Aluno)** – Indicadores de **aprovação** que integram o **IDEB**.
    
    > Observação: **IBGE não será utilizado** neste MVP.
    """
)

st.info("Navegue pelas seções no menu à esquerda para explorar a estrutura. Este MVP não contém dados ainda.")

# =============================
# NAVEGAÇÃO (PLACEHOLDERS)
# =============================
sec = st.sidebar.radio(
    "Seções",
    [
        "Início",
        "Panorama IDEB",
        "Ranking de Municípios",
        "Evolução Temporal",
        "Comparador",
        "Metodologia & Fontes",
    ],
)

# Placeholders vazios apenas para estruturar o app, sem carregar dados
if sec == "Panorama IDEB":
    st.header("Panorama IDEB — Placeholder")
    st.write("Aqui entra o resumo geral do IDEB por município/ano quando os dados forem adicionados.")

elif sec == "Ranking de Municípios":
    st.header("Ranking de Municípios — Placeholder")
    st.write("Tabela/gráfico de ranking por IDEB (maior/menor).")

elif sec == "Evolução Temporal":
    st.header("Evolução Temporal — Placeholder")
    st.write("Séries históricas do IDEB por município e segmento (Anos Iniciais / Anos Finais / EM).")

elif sec == "Comparador":
    st.header("Comparador — Placeholder")
    st.write("Comparação lado a lado de dois municípios para um período selecionado.")

elif sec == "Metodologia & Fontes":
    st.header("Metodologia (resumo)")
    st.markdown(
        """
        - O **IDEB** é composto por **proficiência (Saeb)** e **fluxo (aprovação)**.  
        - Recomenda-se construir um **pipeline de dados** para ingestão dos microdados/planilhas e geração dos indicadores.  
        - Em produção, utilizar checagens de qualidade (cobertura, consistência temporal, outliers) e versionamento (Git).
        """
    )
    st.subheader("Referências")
    st.markdown("INEP: publicações do IDEB, Saeb e Censo Escolar. (Sem uso de bases do IBGE neste MVP.)")

# Rodapé
st.markdown("---")
st.caption("MVP de apresentação — IDEB/ES • Estrutura pronta para receber dados e visualizações.")

