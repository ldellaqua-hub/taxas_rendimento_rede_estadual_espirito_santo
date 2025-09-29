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

st.subheader("Fontes dos Dados (apenas IDEB)")
st.write(
    """
    - **INEP / Saeb** – Proficiências em Língua Portuguesa e Matemática utilizadas na composição do **IDEB**. 
    
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

# =============================
# FUNÇÕES DE CARGA (XLSX)
# =============================
@st.cache_data(show_spinner=False)
def load_xlsx_local(path: str, sheet_name=0) -> pd.DataFrame:
    # Lê direto da raiz do repositório
    return pd.read_excel(path, engine="openpyxl", sheet_name=sheet_name)

def coerce_numeric_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Converte colunas object para numéricas quando possível (troca vírgula por ponto)."""
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == "object":
            try:
                s = df[c].astype(str).str.replace(",", ".", regex=False)
                df[c] = pd.to_numeric(s, errors="coerce")
            except Exception:
                # mantém como está se não for conversível
                pass
    return df

# =============================
# SEÇÃO: INÍCIO
# =============================
if sec == "Início":
    st.title("📈 Painel IDEB – Rede Estadual/ES (por Município)")

    st.markdown(
        """
        Esta aplicação apresenta um MVP (Produto Mínimo Viável) como parte da avaliação da disciplina de **Cloud Computing**
        para produtos de dados na Pós-graduação em **Mineração de Dados**.

        - Professor: **Maxwell Monteiro**  
        - Aluna: **Luciene Dellaqua Bergamin**
        """
    )

    st.subheader("Objetivo do Projeto")
    st.write(
        """
        Criar um painel de apresentação para exploração do **IDEB (Índice de Desenvolvimento da Educação Básica)** da rede 
        estadual do Espírito Santo, com foco em visualizações e comparações **por município**.
        """
    )

    st.subheader("O que é o IDEB (resumo)")
    st.write(
        """
        O IDEB combina **aprendizado** (proficiência medida pelo **Saeb**) e **fluxo escolar** (principalmente a **taxa de aprovação**
        do Censo Escolar). É divulgado bianualmente e pode ser analisado por **rede**, **município** e **escola**.
        """
    )

    st.subheader("Fontes dos Dados (apenas IDEB e Censo Escolar)")
    st.write(
        """
        - **INEP / Saeb** – Proficiências em Língua Portuguesa e Matemática utilizadas na composição do **IDEB**.  
        - **INEP / Censo Escolar (Situação do Aluno)** – Indicadores de **aprovação** que integram o **IDEB**.
        """
    )

# =============================
# SEÇÃO: PANORAMA IDEB (carrega direto da raiz)
# =============================
elif sec == "Panorama IDEB":
    st.header("Panorama IDEB – Ensino Médio (Municípios/ES)")

    try:
        # ⚠️ Arquivo deve estar na RAIZ do repositório com este nome exato
        df = load_xlsx_local("IDEB_ensino_medio_municipios_2023_ES.xlsx", sheet_name=0)
        st.success("Base `IDEB_ensino_medio_municipios_2023_ES.xlsx` carregada da raiz do repositório.")
    except FileNotFoundError:
        st.error("Arquivo `IDEB_ensino_medio_municipios_2023_ES.xlsx` não encontrado na raiz do repositório.")
        st.stop()
    except Exception as e:
        st.error(f"Não foi possível ler o Excel: {e}")
        st.stop()

    # Normaliza cabeçalhos e tenta converter numéricos em texto
    df.columns = [str(c).strip() for c in df.columns]
    df = coerce_numeric_cols(df)

    # Prévia
    st.subheader("🔍 Prévia da Tabela")
    st.dataframe(df.head(20), use_container_width=True)

    # (1) OBRIGATÓRIO: Tabela descritiva
    st.subheader("📈 Estatísticas Descritivas (Pandas `describe()`)")
    desc = df.select_dtypes(include="number").describe().T
    st.dataframe(desc, use_container_width=True)

    # (2) OBRIGATÓRIO: 1 gráfico (barras)
    st.subheader("📊 Gráfico de Barras – municípios x métrica")
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
        plot_df = (
            df[[col_cat, col_y]]
            .dropna()
            .sort_values(col_y, ascending=False)
            .head(n_top)
            .set_index(col_cat)
        )
        st.bar_chart(plot_df)

        with st.expander("Ver dados do gráfico"):
            st.dataframe(plot_df.reset_index(), use_container_width=True)

    st.caption("✔ Requisitos do MVP atendidos: `describe()` + 1 gráfico.")

# =============================
# DEMAIS SEÇÕES (placeholders)
# =============================
elif sec == "Ranking de Municípios":
    st.header("🏆 Ranking de Municípios — Ensino Médio (ES)")

    # 1) Carrega a base (mesmo arquivo na RAIZ)
    try:
        df = load_xlsx_local("IDEB_ensino_medio_municipios_2023_ES.xlsx", sheet_name=0)
    except Exception as e:
        st.error(f"Não foi possível abrir o Excel: {e}")
        st.stop()

    # 2) Limpa cabeçalhos e tipa numéricos
    df.columns = [str(c).strip() for c in df.columns]
    df = coerce_numeric_cols(df)

    # 3) Detecta coluna de município
    muni_cols = [c for c in df.columns
                 if "muni" in c.lower() or "municí" in c.lower() or "municipio" in c.lower()]
    if not muni_cols:
        muni_col = df.columns[0]
        st.warning(f"Não encontrei coluna de município; usando `{muni_col}`.")
    else:
        muni_col = muni_cols[0]

    # 4) Seleção de métrica e opções
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if not num_cols:
        st.error("A base não possui colunas numéricas para ranquear.")
        st.stop()

    sugestoes = [c for c in num_cols if any(k in c.lower() for k in ["ideb", "nota", "índice", "indice", "profici", "aprova"])]
    metrica_default = sugestoes[0] if sugestoes else num_cols[0]

    with st.sidebar:
        st.markdown("### ⚙️ Opções do Ranking")
        metrica = st.selectbox("Métrica:", num_cols, index=num_cols.index(metrica_default))
        ordem = st.radio("Ordenação:", ["Maior → Menor", "Menor → Maior"], index=0, horizontal=True)
        topn = st.slider("Top N", min_value=5, max_value=min(100, len(df)), value=min(20, len(df)))
        termo = st.text_input("Filtrar por nome do município (opcional)")

    # 5) Filtra e ranqueia
    base = df[[muni_col, metrica]].dropna().copy()
    if termo.strip():
        base = base[base[muni_col].astype(str).str.contains(termo.strip(), case=False, na=False)]

    asc = (ordem == "Menor → Maior")
    base = base.sort_values(metrica, ascending=asc, kind="mergesort")
    base["Posição"] = range(1, len(base) + 1)

    ranking = base[["Posição", muni_col, metrica]].head(topn)

    # 6) Exibe tabela e permite download
    st.subheader("📋 Tabela do Ranking")
    st.dataframe(
        ranking.reset_index(drop=True),
        use_container_width=True,
    )

    csv = ranking.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar ranking (CSV)",
        data=csv,
        file_name=f"ranking_municipios_{metrica}.csv",
        mime="text/csv",
    )

    # 7) Gráfico de barras do Top N
    st.subheader("📊 Top N — Gráfico de Barras")
    plot_df = ranking.set_index(muni_col)[metrica]
    st.bar_chart(plot_df)

    # 8) Nota de rodapé
    st.caption(
        "Dica: altere a **métrica** e a **ordenação** no painel lateral. "
        "Use o campo de **filtro** para localizar rapidamente um município."
    )

elif sec == "Evolução Temporal":
    st.header("Evolução Temporal")
    st.info("Em construção.")

elif sec == "Comparador":
    st.header("Comparador")
    st.info("Em construção.")

elif sec == "Metodologia & Fontes":
    st.header("Metodologia & Fontes")
    st.info("Em construção.")