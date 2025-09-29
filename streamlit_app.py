import streamlit as st
import pandas as pd
from io import BytesIO

try:
    import altair as alt
    HAS_ALTAIR = True
except Exception:
    HAS_ALTAIR = False


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

st.info("Navegue pelas seções no menu à esquerda para explorar a estrutura.")

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
    """
    Converte colunas object para numéricas apenas quando fizer sentido.
    - Ignora colunas claramente categóricas (ex.: NO_MUNICIPIO, REDE, SG_UF, UF, NOME, DESCRICAO).
    - Só converte se >= 60% das células virarem número após a tentativa.
    - Troca vírgula por ponto antes de converter.
    """
    df = df.copy()

    # colunas que NUNCA vamos converter para número
    never_numeric = []
    for c in df.columns:
        cl = c.lower()
        if any(k in cl for k in [
            "no_municipio", "município", "municipio",
            "rede", "sg_uf", "uf",
            "nome", "descricao", "descrição", "desc"
        ]):
            never_numeric.append(c)

    for c in df.columns:
        if df[c].dtype == "object" and c not in never_numeric:
            s = df[c].astype(str).str.strip().replace({"": None})
            s = s.str.replace(",", ".", regex=False)

            parsed = pd.to_numeric(s, errors="coerce")
            ratio_numeric = parsed.notna().mean()

            # só converte se maioria virou número
            if ratio_numeric >= 0.60:
                df[c] = parsed
            else:
                df[c] = df[c].astype(str)  # garante texto legível

    return df

def detect_muni_col(df: pd.DataFrame) -> str:
    """Tenta descobrir a coluna de município."""
    candidates = [c for c in df.columns if any(k in c.lower() for k in ["muni", "municí", "municipio"])]
    return candidates[0] if candidates else df.columns[0]

def ffill_text_cols(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preenche para baixo (forward-fill) colunas textuais típicas de planilhas agrupadas,
    como NO_MUNICIPIO, REDE, SG_UF. Só preenche se a coluna existir.
    """
    df = df.copy()
    candidatos = ["NO_MUNICIPIO", "REDE", "SG_UF", "UF", "NOME_MUNICIPIO", "NM_MUNICIPIO"]
    for col in candidatos:
        if col in df.columns:
            df[col] = df[col].ffill()
    return df

# ===== NOVO: normaliza rótulos de 'REDE' e permite filtrar =====
def normalize_rede(value):
    """Padroniza rótulos de rede para facilitar o filtro."""
    if pd.isna(value):
        return value
    t = str(value).strip().lower()
    if t.startswith("estad"):   # estadual, ESTADUAL…
        return "Estadual"
    if t.startswith("munic") or t.startswith("públi") or t.startswith("publi"):
        return "Municipal/Pública"
    if t.startswith("feder"):
        return "Federal"
    if t.startswith("priv"):
        return "Privada"
    return str(value).strip().title()
# ================================================================


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
# SEÇÃO: PANORAMA IDEB
# =============================
elif sec == "Panorama IDEB":
    st.header("Panorama IDEB – Ensino Médio (Municípios/ES)")

    try:
        df = load_xlsx_local("IDEB_ensino_medio_municipios_2023_ES.xlsx", sheet_name=0)
        st.success("Base `IDEB_ensino_medio_municipios_2023_ES.xlsx` carregada da raiz do repositório.")
    except FileNotFoundError:
        st.error("Arquivo `IDEB_ensino_medio_municipios_2023_ES.xlsx` não encontrado na raiz do repositório.")
        st.stop()
    except Exception as e:
        st.error(f"Não foi possível ler o Excel: {e}")
        st.stop()

    # normaliza cabeçalhos, tipa numéricos e preenche textos
    df.columns = [str(c).strip() for c in df.columns]
    df = coerce_numeric_cols(df)
    df = ffill_text_cols(df)

    # ===== NOVO: normaliza e filtra apenas REDE = 'Estadual'
    if "REDE" in df.columns:
        df["REDE"] = df["REDE"].map(normalize_rede)
        df = df[df["REDE"] == "Estadual"].copy()
    # ================================================

    # Prévia
    st.subheader("🔍 Prévia da Tabela")
    st.dataframe(df.head(20), use_container_width=True)

    # (1) OBRIGATÓRIO: Tabela descritiva
    st.subheader("📈 Estatísticas Descritivas (Pandas `describe()`)")
    desc = df.select_dtypes(include="number").describe().T
    st.dataframe(desc, use_container_width=True)

    # (2) Gráfico de barras
    st.subheader("📊 Gráfico de Barras – municípios x métrica")
    muni_col = detect_muni_col(df)
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if not num_cols:
        st.error("Não há colunas numéricas para plotar.")
        st.stop()

    col_cat = st.selectbox("Coluna categórica (X):", df.columns, index=list(df.columns).index(muni_col))
    sugestoes = [c for c in num_cols if any(k in c.lower() for k in ["ideb", "nota", "índice", "indice", "profici", "aprova"])]
    y_default = sugestoes[0] if sugestoes else num_cols[0]
    col_y = st.selectbox("Métrica (Y):", num_cols, index=num_cols.index(y_default))
    n_top = st.slider("Quantidade de municípios (Top N):", 5, min(30, len(df)), min(15, len(df)))

    base = (
        df[[col_cat, col_y]]
        .dropna()
        .assign(**{col_cat: lambda d: d[col_cat].astype(str)})
        .sort_values(col_y, ascending=False)
        .head(n_top)
    )

    if HAS_ALTAIR:
        chart = (
            alt.Chart(base)
            .mark_bar()
            .encode(
                x=alt.X(f"{col_cat}:N", sort='-y', axis=alt.Axis(labelAngle=-40, title=col_cat)),
                y=alt.Y(f"{col_y}:Q", title=col_y),
                tooltip=[col_cat, col_y],
            )
            .properties(height=420)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.bar_chart(base, x=col_cat, y=col_y)

    with st.expander("Ver dados do gráfico"):
        st.dataframe(base, use_container_width=True)

    st.caption("✔ Requisitos do MVP atendidos: `describe()` + 1 gráfico.")

# =============================
# SEÇÃO: RANKING DE MUNICÍPIOS
# =============================
elif sec == "Ranking de Municípios":
    st.header("🏆 Ranking de Municípios — Ensino Médio (ES)")

    try:
        df = load_xlsx_local("IDEB_ensino_medio_municipios_2023_ES.xlsx", sheet_name=0)
    except Exception as e:
        st.error(f"Não foi possível abrir o Excel: {e}")
        st.stop()

    df.columns = [str(c).strip() for c in df.columns]
    df = coerce_numeric_cols(df)
    df = ffill_text_cols(df)

    # ===== NOVO: normaliza e filtra apenas REDE = 'Estadual'
    if "REDE" in df.columns:
        df["REDE"] = df["REDE"].map(normalize_rede)
        df = df[df["REDE"] == "Estadual"].copy()
    # ================================================

    muni_col = detect_muni_col(df)
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

    base = df[[muni_col, metrica]].dropna().copy()
    base[muni_col] = base[muni_col].astype(str)
    if termo.strip():
        base = base[base[muni_col].str.contains(termo.strip(), case=False, na=False)]

    asc = (ordem == "Menor → Maior")
    base = base.sort_values(metrica, ascending=asc, kind="mergesort")
    base["Posição"] = range(1, len(base) + 1)
    ranking = base[["Posição", muni_col, metrica]].head(topn)

    st.subheader("📋 Tabela do Ranking")
    st.dataframe(ranking.reset_index(drop=True), use_container_width=True)

    csv = ranking.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Baixar ranking (CSV)", data=csv,
                       file_name=f"ranking_municipios_{metrica}.csv", mime="text/csv")

    st.subheader("📊 Top N — Gráfico de Barras")
    gdf = ranking.rename(columns={muni_col: "Município"})
    gdf["Município"] = gdf["Município"].astype(str)

    if HAS_ALTAIR:
        chart = (
            alt.Chart(gdf)
            .mark_bar()
            .encode(
                x=alt.X("Município:N", sort='-y', axis=alt.Axis(labelAngle=-40)),
                y=alt.Y(f"{metrica}:Q"),
                tooltip=["Posição", "Município", metrica],
            )
            .properties(height=420)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.bar_chart(gdf, x="Município", y=metrica)

    st.caption("Dica: ajuste a métrica, a ordenação e use o filtro para localizar um município.")

# =============================
# PLACEHOLDERS
# =============================
elif sec == "Comparador":
    st.header("Comparador")
    st.info("Em construção.")



elif sec == "Metodologia & Fontes":
    st.header("Metodologia & Fontes")
    st.info("Em construção.")