import streamlit as st
import pandas as pd
from io import BytesIO




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

# -------------------------
# Funções de carga (xlsx)
# -------------------------
@st.cache_data(show_spinner=False)
def load_xlsx_bytes(file_bytes: bytes, sheet_name=0) -> pd.DataFrame:
    return pd.read_excel(BytesIO(file_bytes), engine="openpyxl", sheet_name=sheet_name)

@st.cache_data(show_spinner=False)
def load_xlsx_local(path: str, sheet_name=0) -> pd.DataFrame:
    return pd.read_excel(path, engine="openpyxl", sheet_name=sheet_name)


# -------------------------
# Seção: PANORAMA IDEB (carrega direto da raiz)
# -------------------------
if sec == "Panorama IDEB":
    st.header("Panorama IDEB – Ensino Médio (Municípios/ES)")

    try:
        df = load_xlsx_local("IDEB_ensino_medio_municipios_2023_ES.xlsx", sheet_name=0)
        st.success("Base IDEB_ensino_medio_municipios_2023_ES.xlsx carregada da raiz do repositório.")
    except FileNotFoundError:
        st.error("Arquivo `IDEB_ensino_medio_municipios_2023_ES.xlsx` não encontrado na raiz do repositório.")
        st.stop()
    except Exception as e:
        st.error(f"Não foi possível ler o Excel: {e}")
        st.stop()

    # Normaliza cabeçalhos
    df.columns = [str(c).strip() for c in df.columns]

    st.subheader("Prévia da Tabela")
    st.dataframe(df.head(20), use_container_width=True)

    # (1) OBRIGATÓRIO: Tabela descritiva
    st.subheader("Estatísticas Descritivas (Pandas `describe()`)") 
    desc = df.describe(numeric_only=True).T
    st.dataframe(desc, use_container_width=True)

    # (2) OBRIGATÓRIO: 1 gráfico (barras)
    st.subheader("Gráfico de Barras – municípios x métrica")
    possiveis_cat = [c for c in df.columns if "muni" in c.lower() or "municí" in c.lower() or "municipio" in c.lower()]
    col_x = possiveis_cat[0] if possiveis_cat else df.columns[0]

    col_cat = st.selectbox("Coluna categórica (eixo X):", df.columns, index=list(df.columns).index(col_x))
    numericas = df.select_dtypes(include="number").columns.tolist()
    if not numericas:
        st.error("Não há colunas numéricas para plotar.")
    else:
        sugestoes = [c for c in numericas if "ideb" in c.lower() or "nota" in c.lower() or "índice" in c.lower() or "indice" in c.lower()]
        y_default = sugestoes[0] if sugestoes else numericas[0]
        col_y = st.selectbox("Métrica (eixo Y):", numericas, index=numericas.index(y_default))

        n_top = st.slider("Quantidade de municípios (Top N):", 5, min(30, len(df)), min(15, len(df)))
        plot_df = (df[[col_cat, col_y]]
                   .dropna()
                   .sort_values(col_y, ascending=False)
                   .head(n_top)
                   .set_index(col_cat))
        st.bar_chart(plot_df)

        with st.expander("Ver dados do gráfico"):
            st.dataframe(plot_df.reset_index(), use_container_width=True)

    st.caption("✔ Requisitos do MVP atendidos: `describe()` + 1 gráfico.")