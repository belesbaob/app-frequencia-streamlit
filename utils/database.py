import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import os

# Arquivos de dados
USERS_FILE = "data/users.csv"
TURMAS_FILE = "data/turmas.csv"
ALUNOS_FILE = "data/alunos.csv"
FREQUENCIA_FILE = "data/frequencia.csv"

# Dados de login
USERS = {
    "admin": "admin",
    "professor1": "prof123",
    "professor2": "prof456"
}

# Função para autenticação e conexão com o Google Sheets
def get_gspread_client():
    # Carrega as credenciais do Streamlit Secrets
    credentials_dict = st.secrets.get("gcp_service_account")
    
    if credentials_dict:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(
            credentials_dict, scopes=scopes
        )
        return gspread.authorize(credentials)
    else:
        st.error("Credenciais do Google Sheets não encontradas. Verifique suas secrets.")
        return None

def get_data(file_name):
    """Lê dados de um arquivo CSV ou do Google Sheets."""
    if st.secrets.get("use_google_sheets") and get_gspread_client():
        try:
            client = get_gspread_client()
            sheet = client.open_by_key(st.secrets["google_sheets_key"])
            worksheet = sheet.worksheet(file_name)
            return pd.DataFrame(worksheet.get_all_records())
        except Exception as e:
            st.error(f"Erro ao ler do Google Sheets: {e}")
            return pd.DataFrame()
    
    try:
        df = pd.read_csv(file_name)
        return df
    except FileNotFoundError:
        return pd.DataFrame()

def save_data(df, file_name):
    """Salva dados em um arquivo CSV ou no Google Sheets."""
    if st.secrets.get("use_google_sheets") and get_gspread_client():
        try:
            client = get_gspread_client()
            sheet = client.open_by_key(st.secrets["google_sheets_key"])
            worksheet = sheet.worksheet(file_name)
            worksheet.clear()
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())
            st.success(f"Dados salvos no Google Sheets: {file_name}")
            return
        except Exception as e:
            st.error(f"Erro ao salvar no Google Sheets: {e}")
            return

    df.to_csv(file_name, index=False)
    st.success(f"Dados salvos em {file_name}")

def setup_files():
    """Configura os arquivos CSV (se não existirem)."""
    if not os.path.exists('data'):
        os.makedirs('data')
    
    if not os.path.exists(USERS_FILE):
        users_df = pd.DataFrame(USERS.items(), columns=['username', 'password'])
        users_df.to_csv(USERS_FILE, index=False)
        st.info("Arquivo de usuários criado.")
    
    # Adicione a lógica de criação para outros arquivos aqui, se necessário
    if not os.path.exists(TURMAS_FILE):
        turmas_df = pd.DataFrame(columns=['id_turma', 'nome_turma'])
        turmas_df.to_csv(TURMAS_FILE, index=False)
        st.info("Arquivo de turmas criado.")

    if not os.path.exists(ALUNOS_FILE):
        alunos_df = pd.DataFrame(columns=['id_aluno', 'nome', 'turma'])
        alunos_df.to_csv(ALUNOS_FILE, index=False)
        st.info("Arquivo de alunos criado.")
    
    if not os.path.exists(FREQUENCIA_FILE):
        frequencia_df = pd.DataFrame(columns=['id_aluno', 'data', 'status', 'justificativa', 'professor'])
        frequencia_df.to_csv(FREQUENCIA_FILE, index=False)
        st.info("Arquivo de frequência criado.")

def get_alunos_by_turma(turma):
    """Retorna os alunos de uma turma específica."""
    df_alunos = get_data(ALUNOS_FILE)
    if not df_alunos.empty:
        return df_alunos[df_alunos['turma'] == turma]
    return pd.DataFrame()