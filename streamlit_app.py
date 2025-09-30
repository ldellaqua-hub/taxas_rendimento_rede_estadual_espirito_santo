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

def _muni_name_col(df: pd.DataFrame) -> str | None:
    prefer = ["NO_MUNICIPIO", "NOME_MUNICIPIO", "NM_MUNICIPIO", "MUNICIPIO"]
    for c in prefer:
        if c in df.columns:
            return c
    # genérico: qualquer coluna com "muni" que NÃO comece com CO/CD/COD/ID
    for c in df.columns:
        cl = str(c).lower()
        if "muni" in cl and not (cl.startswith("co_") or cl.startswith("cd_")
                                 or cl.startswith("cod") or cl.startswith("id_")):
            return c
    return None

def _muni_code_col(df: pd.DataFrame) -> str | None:
    prefer = ["CO_MUNICIPIO", "CD_MUNICIPIO", "COD_MUNICIPIO", "ID_MUNICIPIO"]
    for c in prefer:
        if c in df.columns:
            return c
    for c in df.columns:
        if "co_municipio" in str(c).lower():
            return c
    return None

def get_muni_label_col(df: pd.DataFrame) -> tuple[str | None, str]:
    """
    Retorna (coluna_codigo, coluna_para_exibir).
    Se houver coluna de nome, usa ela para exibir; senão usa a de código.
    """
    code = _muni_code_col(df)
    name = _muni_name_col(df)
    label = name or code or df.columns[0]
    return code, label



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

# ===== Helper robusto para converter várias colunas em numéricas =====
from pandas.api.types import is_numeric_dtype
import numpy as np
import pandas as pd

def _coerce_block(d: pd.DataFrame, cols) -> pd.DataFrame:
    """
    Converte para numérico as colunas indicadas.
    - Aceita listas aninhadas (ex.: cols_x + cols_y).
    - Funciona mesmo com NOMES DUPLICADOS, iterando por posição.
    - Trata vírgula decimal e nulos textuais: '-', 'None', 'nan', 'NA', ''.
    """
    d = d.copy()

    # 1) Achata 'cols'
    flat_cols = []
    if isinstance(cols, (list, tuple, pd.Index, np.ndarray)):
        for c in cols:
            if isinstance(c, (list, tuple, pd.Index, np.ndarray)):
                flat_cols.extend(list(c))
            else:
                flat_cols.append(c)
    else:
        flat_cols = [cols]

    # 2) Mantém só rótulos que existem
    flat_cols = [c for c in flat_cols if c in d.columns]
    if not flat_cols:
        return d

    # 3) Para cada rótulo, converte TODAS as posições onde ele aparece
    cols_array = np.array(d.columns, dtype=object)
    for name in flat_cols:
        positions = np.where(cols_array == name)[0].tolist()  # lida com duplicados
        for pos in positions:
            s = d.iloc[:, pos]
            if not is_numeric_dtype(s):
                s = s.astype(str)
                s = s.str.replace(",", ".", regex=False)
                s = s.replace({"-": None, "None": None, "nan": None, "NA": None, "": None})
            d.iloc[:, pos] = pd.to_numeric(s, errors="coerce")

    return d




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
elif sec == "Evolução Temporal":
    st.header("📈 Evolução Temporal — Ensino Médio (ES)")

    # 1) Carregar e preparar a base
    try:
        df = load_xlsx_local("IDEB_ensino_medio_municipios_2023_ES.xlsx", sheet_name=0)
    except Exception as e:
        st.error(f"Não foi possível abrir o Excel: {e}")
        st.stop()

    df.columns = [str(c).strip() for c in df.columns]
    df = coerce_numeric_cols(df)
    df = ffill_text_cols(df)

    # Filtra só rede Estadual (como nas outras seções)
    if "REDE" in df.columns:
        df["REDE"] = df["REDE"].map(normalize_rede)
        df = df[df["REDE"] == "Estadual"].copy()

    muni_col = detect_muni_col(df)

    # 2) Descobrir famílias de colunas com ANO no nome
    import re
    cols_com_ano = [c for c in df.columns if re.search(r"20\d{2}", c)]
    if not cols_com_ano:
        st.warning("Não encontrei colunas com ano no nome (padrão 20XX).")
        st.stop()

    def familia(col):
        return re.split(r"20\d{2}", col)[0].rstrip("_")

    familias = {}
    for c in cols_com_ano:
        fam = familia(c)
        familias.setdefault(fam, []).append(c)

    familias_ordenadas = sorted(familias.keys())

    # 3) Opções do usuário
    with st.sidebar:
        st.markdown("### ⚙️ Opções — Evolução")
        fam_escolhida = st.selectbox("Família da métrica:", familias_ordenadas)
        municipios = sorted(df[muni_col].dropna().astype(str).unique().tolist())
        sel_munis = st.multiselect(
            "Municípios (1 ou mais):",
            municipios,
            default=municipios[:3] if len(municipios) >= 3 else municipios
        )
        mostrar_media_estado = st.checkbox("Incluir média do Estado (entre municípios selecionados)")

    if not sel_munis:
        st.info("Selecione ao menos um município.")
        st.stop()

    # 4) Criar tabela "longa" (ano, valor) para a família escolhida
    cols_familia = familias[fam_escolhida]
    base = df[df[muni_col].astype(str).isin(sel_munis)][[muni_col] + cols_familia].copy()
    base[muni_col] = base[muni_col].astype(str)

    long_rows = []
    for c in cols_familia:
        anos = re.findall(r"(20\d{2})", c)
        if not anos:
            continue
        ano = int(anos[0])
        tmp = base[[muni_col, c]].rename(columns={c: "valor"})

        # 🔧 LIMPEZA CRÍTICA: força numérico e trata traços/strings
        tmp["valor"] = (
            tmp["valor"]
            .replace({"-": None, "None": None, "nan": None, "NA": None})
        )
        tmp["valor"] = pd.to_numeric(tmp["valor"], errors="coerce")

        tmp["ano"] = ano
        long_rows.append(tmp)

    if not long_rows:
        st.warning("Não foi possível extrair anos das colunas da família selecionada.")
        st.stop()

    long_df = pd.concat(long_rows, ignore_index=True)

    # remove linhas sem valor numérico
    long_df = long_df.dropna(subset=["valor"])

    # Se houver várias colunas no mesmo ano (ex.: _2017_1.._4), agrega por média
    long_df = (
        long_df
        .groupby([muni_col, "ano"], as_index=False, sort=True)["valor"]
        .mean()  # agora é seguro, só tem número
        .sort_values(["ano", muni_col])
    )

    if long_df.empty:
        st.warning("Sem valores numéricos válidos para a combinação escolhida.")
        st.stop()

    # 5) Plot
    st.subheader(f"📊 Série temporal — {fam_escolhida}")
    if HAS_ALTAIR:
        chart = (
            alt.Chart(long_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("ano:O", title="Ano", sort="ascending"),
                y=alt.Y("valor:Q", title=f"{fam_escolhida}"),
                color=alt.Color(f"{muni_col}:N", title="Município"),
                tooltip=[muni_col, "ano", alt.Tooltip("valor:Q", format=".3f")],
            )
            .properties(height=420)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        pivot = long_df.pivot(index="ano", columns=muni_col, values="valor").sort_index()
        st.line_chart(pivot)

    # 6) (Opcional) média estadual (entre municípios selecionados)
    if mostrar_media_estado and HAS_ALTAIR:
        medias = long_df.groupby("ano", as_index=False)["valor"].mean()
        media_chart = (
            alt.Chart(medias)
            .mark_line(point=True, strokeDash=[6, 3], color="black")
            .encode(x="ano:O", y="valor:Q", tooltip=[alt.Tooltip("valor:Q", format=".3f"), "ano"])
        )
        st.altair_chart(chart + media_chart, use_container_width=True)

    # 7) Tabela e download
    st.subheader("🗂️ Dados (formato long)")
    st.dataframe(long_df, use_container_width=True)
    st.download_button(
        "⬇️ Baixar CSV da série",
        data=long_df.to_csv(index=False).encode("utf-8"),
        file_name=f"serie_temporal_{fam_escolhida}.csv",
        mime="text/csv",
    )

    st.caption(
        "Observação: quando há múltiplas colunas no mesmo ano (ex.: 2017_1, 2017_2, 2017_3, 2017_4), "
        "o valor anual mostrado é a **média** dessas colunas."
    )

# =============================
# SEÇÃO: COMPARADOR
# =============================
# =============================
# SEÇÃO: COMPARADOR
# =============================
elif sec == "Comparador":
    st.header("🔀 Comparador de Municípios — Ensino Médio (ES)")

    import re

    # 1) Carrega e prepara a base
    try:
        df = load_xlsx_local("IDEB_ensino_medio_municipios_2023_ES.xlsx", sheet_name=0)
    except Exception as e:
        st.error(f"Não foi possível abrir o Excel: {e}")
        st.stop()

    df.columns = [str(c).strip() for c in df.columns]
    df = coerce_numeric_cols(df)
    df = ffill_text_cols(df)

    # Mantém somente REDE = Estadual (e normaliza rótulos da coluna)
    if "REDE" in df.columns:
        df["REDE"] = df["REDE"].map(normalize_rede)
        df = df[df["REDE"] == "Estadual"].copy()

    muni_col = detect_muni_col(df)

    # 2) Descobre famílias de colunas que contêm ano (20XX) no nome
    cols_com_ano = [c for c in df.columns if re.search(r"20\d{2}", c)]
    if not cols_com_ano:
        st.warning("Não encontrei colunas com ano no nome (padrão 20XX).")
        st.stop()

    def familia(col: str) -> str:
        """Retorna o prefixo antes do ano (ex.: VL_APROVACAO_2017 -> VL_APROVACAO)."""
        return re.split(r"20\d{2}", col)[0].rstrip("_")

    # famílias -> {familia: {ano: [colunas...]}}
    familias: dict[str, dict[int, list[str]]] = {}
    for c in cols_com_ano:
        fam = familia(c)
        yr = int(re.findall(r"(20\d{2})", c)[0])
        familias.setdefault(fam, {}).setdefault(yr, []).append(c)

    familias_ordenadas = sorted(familias.keys())

    # 3) Filtros laterais
    with st.sidebar:
        st.markdown("### ⚙️ Opções — Comparador")
        municipios = sorted(df[muni_col].dropna().astype(str).unique().tolist())
        sel_munis = st.multiselect(
            "Municípios (2+):",
            municipios,
            default=municipios[:5] if len(municipios) >= 5 else municipios
        )

    if len(sel_munis) < 2:
        st.info("Selecione **pelo menos 2 municípios** para comparar.")
        st.stop()

    # 4) Abas
    tab_bar, tab_scatter = st.tabs(["📊 Barras (1 métrica)", "🔎 Dispersão (2 métricas)"])

    # ----------------- ABA 1: BARRAS -----------------
    with tab_bar:
        st.subheader("📊 Barras — uma métrica em um ano")
        col1, col2, col3 = st.columns(3)
        with col1:
            fam1 = st.selectbox("Família da métrica:", familias_ordenadas, key="cmp_fam1")
        anos_fam1 = sorted(familias[fam1].keys())
        with col2:
            ano1 = st.selectbox("Ano:", anos_fam1, index=len(anos_fam1)-1, key="cmp_ano1")
        with col3:
            topn = st.slider("Top N (após filtro de municípios):", 2, min(50, len(sel_munis)), min(10, len(sel_munis)))

        cols_ano1 = familias[fam1][ano1]
        base = df[df[muni_col].astype(str).isin(sel_munis)][[muni_col] + cols_ano1].copy()
        base[muni_col] = base[muni_col].astype(str)

        # ✅ usa o helper definido no topo do arquivo
        base = _coerce_block(base, cols_ano1)

        comp = (
            base
            .assign(valor=base[cols_ano1].mean(axis=1, skipna=True))
            [[muni_col, "valor"]]
            .dropna(subset=["valor"])
            .groupby(muni_col, as_index=False)["valor"].mean()
            .sort_values("valor", ascending=False)
        )
        comp_top = comp.head(topn)

        if HAS_ALTAIR:
            chart = (
                alt.Chart(comp_top)
                .mark_bar()
                .encode(
                    x=alt.X(f"{muni_col}:N", sort='-y', axis=alt.Axis(labelAngle=-40, title="Município")),
                    y=alt.Y("valor:Q", title=f"{fam1} — {ano1}"),
                    tooltip=[muni_col, alt.Tooltip("valor:Q", format=".3f")],
                )
                .properties(height=420)
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.bar_chart(comp_top.set_index(muni_col)["valor"])

        st.dataframe(comp_top.reset_index(drop=True), use_container_width=True)
        st.download_button(
            "⬇️ Baixar CSV (barras)",
            data=comp_top.to_csv(index=False).encode("utf-8"),
            file_name=f"comparador_barras_{fam1}_{ano1}.csv",
            mime="text/csv",
        )

    # ----------------- ABA 2: DISPERSÃO -----------------
    with tab_scatter:
        st.subheader("🔎 Dispersão — duas métricas (X vs Y)")

        c1, c2 = st.columns(2)
        with c1:
            fam_x = st.selectbox("Família (eixo X):", familias_ordenadas, key="cmp_fam_x")
            anos_x = sorted(familias[fam_x].keys())
            ano_x = st.selectbox("Ano (X):", anos_x, index=len(anos_x)-1, key="cmp_ano_x")
        with c2:
            fam_y = st.selectbox("Família (eixo Y):", familias_ordenadas, key="cmp_fam_y")
            anos_y = sorted(familias[fam_y].keys())
            ano_y = st.selectbox("Ano (Y):", anos_y, index=len(anos_y)-1, key="cmp_ano_y")

        cols_x = familias[fam_x][ano_x]
        cols_y = familias[fam_y][ano_y]
        cols_all = cols_x + cols_y

        base = df[df[muni_col].astype(str).isin(sel_munis)][[muni_col] + cols_all].copy()
        base[muni_col] = base[muni_col].astype(str)

        # ✅ usa o helper para garantir numérico nas colunas escolhidas
        base = _coerce_block(base, cols_all)

        base["X"] = base[cols_x].mean(axis=1, skipna=True)
        base["Y"] = base[cols_y].mean(axis=1, skipna=True)

        scatter_df = (
            base[[muni_col, "X", "Y"]]
            .dropna(subset=["X", "Y"])
            .groupby(muni_col, as_index=False)[["X", "Y"]].mean()
        )

        if scatter_df.empty:
            st.warning("Sem dados numéricos suficientes para a combinação escolhida.")
        else:
            if HAS_ALTAIR:
                sc = (
                    alt.Chart(scatter_df)
                    .mark_circle(size=120)
                    .encode(
                        x=alt.X("X:Q", title=f"{fam_x} — {ano_x}"),
                        y=alt.Y("Y:Q", title=f"{fam_y} — {ano_y}"),
                        tooltip=[muni_col, alt.Tooltip("X:Q", format=".3f"), alt.Tooltip("Y:Q", format=".3f")],
                    )
                )
                labels = (
                    alt.Chart(scatter_df)
                    .mark_text(align="left", dx=7, dy=3)
                    .encode(x="X:Q", y="Y:Q", text=f"{muni_col}:N")
                )
                st.altair_chart(sc + labels, use_container_width=True)
            else:
                st.scatter_chart(scatter_df.set_index(muni_col))

            st.dataframe(scatter_df, use_container_width=True)
            st.download_button(
                "⬇️ Baixar CSV (dispersão)",
                data=scatter_df.to_csv(index=False).encode("utf-8"),
                file_name=f"comparador_disp_{fam_x}_{ano_x}_vs_{fam_y}_{ano_y}.csv",
                mime="text/csv",
            )

    st.caption(
        "Barras: se houver múltiplas colunas para o mesmo ano (ex.: 2017_1…2017_4), usamos a **média**. "
        "Dispersão: cada eixo usa a média da família/ano escolhidos."
    )



# =============================
# SEÇÃO: METODOLOGIA
# =============================
elif sec == "Metodologia & Fontes":
    st.header("Metodologia & Fontes")
    st.markdown(
        """
        - **Fonte**: INEP/SAEB (proficiências) e indicadores do IDEB.  
        - **Tratamento**: normalização de rótulos de rede, conversão robusta de colunas numéricas, 
          preenchimento forward-fill em colunas textuais agrupadas e uso de médias quando uma métrica 
          se repete em múltiplas colunas por ano.
        """
    )






