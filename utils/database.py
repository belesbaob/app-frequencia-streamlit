import streamlit as st
import gspread
from gspread.auth import authorized_client
import pandas as pd
from gspread_dataframe import set_with_dataframe, get_as_dataframe

# Credenciais de acesso ao Google Sheets (tokens OAuth)
@st.cache_resource
def get_gspread_client():
    creds = st.secrets["oauth"]
    gc = gspread.authorize(authorized_client(
        credentials=creds,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    ))
    return gc

gc = get_gspread_client()
sh = gc.open("FrequenciaEscolar") # Nome da sua planilha

# Funções de leitura e gravação
def get_data(worksheet_name):
    """Lê os dados de uma aba e retorna um DataFrame."""
    worksheet = sh.worksheet(worksheet_name)
    df = get_as_dataframe(worksheet, header=0)
    df = df.dropna(how='all')
    return df

def save_data(df, worksheet_name):
    """Salva um DataFrame em uma aba do Google Sheets."""
    worksheet = sh.worksheet(worksheet_name)
    worksheet.clear()
    set_with_dataframe(worksheet, df)


def get_alunos_by_turma(turma):
    """Retorna a lista de alunos de uma turma específica."""
    df_alunos = get_data(ALUNOS_FILE)
    return df_alunos[df_alunos['turma'] == turma]

# Exemplo de dados para simular o login
USERS = {
    "Janecleide": {"password": "jane123", "role": "professor"},
    "Daniele": {"password": "daniele123", "role": "professor"},
    "Lucas": {"password": "lucaslemos123", "role": "professor"},
    "sec": {"password": "bist9080", "role": "admin"},
    "deangelis": {"password": "bae2025", "role": "coordenador"},
    "Crislania": {"password": "cris123", "role": "agente"}
}