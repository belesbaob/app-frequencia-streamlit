import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# Arquivos de dados
USERS_FILE = "data/users.csv"
TURMAS_FILE = "data/turmas.csv"
ALUNOS_FILE = "data/alunos.csv"
FREQUENCIA_FILE = "data/frequencia.csv"

# Função para autenticação e conexão com o Google Sheets
def get_gspread_client():
    # Carrega as credenciais do Streamlit Secrets
    credentials_dict = st.secrets["gcp_service_account"]
    
    # Define os escopos necessários
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Cria as credenciais a partir do dicionário de secrets
    credentials = Credentials.from_service_account_info(
        credentials_dict, scopes=scopes
    )
    
    # Retorna o cliente autenticado
    return gspread.authorize(credentials)

def get_data(file_name):
    """Lê dados de um arquivo CSV."""
    # Lógica de fallback para Google Sheets
    if st.secrets.get("use_google_sheets"):
        try:
            client = get_gspread_client()
            sheet = client.open_by_key(st.secrets["google_sheets_key"])
            worksheet = sheet.worksheet(file_name) # Assume que o nome da aba é o nome do arquivo
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
    """Salva dados em um arquivo CSV."""
    if st.secrets.get("use_google_sheets"):
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
    if not os.path.exists(USERS_FILE):
        users_df = pd.DataFrame(USERS)
        save_data(users_df, USERS_FILE)

    # Adicione a lógica de criação para outros arquivos aqui, se necessário

def get_alunos_by_turma(turma):
    """Retorna os alunos de uma turma específica."""
    df_alunos = get_data(ALUNOS_FILE)
    return df_alunos[df_alunos['turma'] == turma]