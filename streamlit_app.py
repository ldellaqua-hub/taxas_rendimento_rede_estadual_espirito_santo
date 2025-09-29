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
# FUNÇÕES DE CARGA (XLSX)
# =============================
@st.cache_data(show_spinner=False)
def load_xlsx_bytes(file_bytes: bytes, sheet_name=0) -> pd.DataFrame:
    return pd.read_excel(BytesIO(file_bytes), engine="openpyxl", sheet_name=sheet_name)

@st.cache_data(show_spinner=False)
def load_xlsx_local(path: str, sheet_name=0) -> pd.DataFrame:
    # >>> Agora procura direto na raiz
    return pd.read_excel(path, engine="openpyxl", sheet_name=sheet_name)

# =============================
# SEÇÃO: PANORAMA IDEB
# =============================
elif secao == "Panorama IDEB":
    st.header("Panorama IDEB – Ensino Médio (Municípios/ES)")

    st.markdown(
        "Use o **uploader** abaixo **ou** marque a opção para carregar o arquivo "
        "`IDEB_ensino_medio_municipios_2023_ES.xlsx` versionado no repositório (raiz)."
    )

    up = st.file_uploader("Enviar base (.xlsx)", type=["xlsx"])
    df = None

    if up is not None:
        try:
            df = load_xlsx_bytes(up.read(), sheet_name=0)
            st.success("Base carregada via upload.")
        except Exception as e:
            st.error(f"Erro lendo o .xlsx enviado: {e}")

    usar_local = st.checkbox("Usar arquivo local do repositório (raiz)")
    if usar_local and df is None:
        try:
            # >>> Caminho atualizado: sem a pasta data/
            df = load_xlsx_local("IDEB_ensino_medio_municipios_2023_ES.xlsx", sheet_name=0)
            st.success("Base carregada do repositório (raiz).")
        except Exception as e:
            st.warning("Não encontrei `IDEB_ensino_medio_municipios_2023_ES.xlsx` na raiz do repositório.")
