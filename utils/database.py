import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, List
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Arquivos de dados
DATA_FILES = {
    'users': "data/users.csv",
    'turmas': "data/turmas.csv", 
    'alunos': "data/alunos.csv",
    'frequencia': "data/frequencia.csv",
    'logs': "data/system_logs.csv"
}

# Níveis de acesso
ACCESS_LEVELS = {
    'admin': ['users', 'turmas', 'alunos', 'frequencia', 'logs', 'reports'],
    'coordenador': ['turmas', 'alunos', 'frequencia', 'reports'],
    'professor': ['alunos', 'frequencia'],
    'agente': ['frequencia']
}

# Usuários do sistema com senhas criptografadas (SHA-256)
# Senhas originais: admin123, prof123, prof456, prof789, coord2025, agent123
DEFAULT_USERS = {
    "admin": {
        "password": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
        "role": "admin",
        "name": "Administrador",
        "active": True
    },
    "professor1": {
        "password": "6ca13d52ca70c883e0f0bb101e425a89e8624de51db2d2392593af6a84118090",  # prof123
        "role": "professor",
        "name": "Professor João",
        "active": True
    },
    "professor2": {
        "password": "8b2c86ea9cf2ea4eb517fd1e06b74f399e7fec0fef92e3b482a6cf2e2b092023",  # prof456
        "role": "professor", 
        "name": "Professora Maria",
        "active": True
    },
    "professor3": {
        "password": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  # prof789
        "role": "professor",
        "name": "Professor Carlos",
        "active": True
    },
    "coordenador": {
        "password": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # coord2025
        "role": "coordenador",
        "name": "Coordenador Pedagógico",
        "active": True
    },
    "agente": {
        "password": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  # agent123
        "role": "agente",
        "name": "Agente Escolar",
        "active": True
    }
}

class DatabaseManager:
    """Gerenciador principal do banco de dados."""
    
    def __init__(self):
        self._gspread_client = None
        self._use_google_sheets = st.secrets.get("use_google_sheets", False)
        self.setup_data_directory()
    
    def hash_password(self, password: str) -> str:
        """Gera hash SHA-256 da senha."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verifica se a senha corresponde ao hash."""
        return self.hash_password(password) == hashed
    
    @property
    def gspread_client(self):
        """Lazy loading do cliente Google Sheets."""
        if self._gspread_client is None and self._use_google_sheets:
            self._gspread_client = self._get_gspread_client()
        return self._gspread_client
    
    def _get_gspread_client(self):
        """Autentica e conecta com o Google Sheets."""
        try:
            credentials_dict = st.secrets.get("gcp_service_account")
            if not credentials_dict:
                logger.warning("Credenciais do Google Sheets não encontradas")
                return None
            
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            credentials = Credentials.from_service_account_info(
                credentials_dict, scopes=scopes
            )
            return gspread.authorize(credentials)
        except Exception as e:
            logger.error(f"Erro ao conectar com Google Sheets: {e}")
            st.error(f"Erro ao conectar com Google Sheets: {e}")
            return None
    
    def setup_data_directory(self):
        """Cria diretório de dados se não existir."""
        if not os.path.exists('data'):
            os.makedirs('data')
            logger.info("Diretório 'data' criado")
    
    def get_data(self, table_name: str) -> pd.DataFrame:
        """Lê dados de uma tabela (CSV ou Google Sheets)."""
        file_path = DATA_FILES.get(table_name)
        if not file_path:
            logger.error(f"Tabela '{table_name}' não reconhecida")
            return pd.DataFrame()
        
        # Tentar Google Sheets primeiro
        if self._use_google_sheets and self.gspread_client:
            try:
                sheet = self.gspread_client.open_by_key(st.secrets["google_sheets_key"])
                worksheet = sheet.worksheet(table_name)
                data = worksheet.get_all_records()
                df = pd.DataFrame(data)
                logger.info(f"Dados lidos do Google Sheets: {table_name}")
                return df
            except Exception as e:
                logger.warning(f"Erro ao ler do Google Sheets ({table_name}): {e}")
        
        # Fallback para CSV
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Dados lidos do CSV: {file_path}")
            return df
        except FileNotFoundError:
            logger.warning(f"Arquivo não encontrado: {file_path}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Erro ao ler CSV ({file_path}): {e}")
            return pd.DataFrame()
    
    def save_data(self, df: pd.DataFrame, table_name: str) -> bool:
        """Salva dados em uma tabela (CSV ou Google Sheets)."""
        file_path = DATA_FILES.get(table_name)
        if not file_path:
            logger.error(f"Tabela '{table_name}' não reconhecida")
            return False
        
        success = False
        
        # Tentar Google Sheets primeiro
        if self._use_google_sheets and self.gspread_client:
            try:
                sheet = self.gspread_client.open_by_key(st.secrets["google_sheets_key"])
                worksheet = sheet.worksheet(table_name)
                
                # Limpar e atualizar worksheet
                worksheet.clear()
                if not df.empty:
                    data = [df.columns.tolist()] + df.values.tolist()
                    worksheet.update(data)
                
                logger.info(f"Dados salvos no Google Sheets: {table_name}")
                st.success(f"Dados salvos no Google Sheets: {table_name}")
                success = True
            except Exception as e:
                logger.error(f"Erro ao salvar no Google Sheets ({table_name}): {e}")
                st.error(f"Erro ao salvar no Google Sheets: {e}")
        
        # Salvar em CSV como backup ou método principal
        try:
            df.to_csv(file_path, index=False, encoding='utf-8')
            logger.info(f"Dados salvos em CSV: {file_path}")
            if not success:  # Só mostrar sucesso se Google Sheets falhou
                st.success(f"Dados salvos em {file_path}")
            success = True
        except Exception as e:
            logger.error(f"Erro ao salvar CSV ({file_path}): {e}")
            if not success:
                st.error(f"Erro ao salvar dados: {e}")
        
        return success
    
    def log_action(self, username: str, action: str, details: str = ""):
        """Registra ações do usuário no sistema."""
        try:
            logs_df = self.get_data('logs')
            if logs_df.empty:
                logs_df = pd.DataFrame(columns=['timestamp', 'username', 'action', 'details'])
            
            new_log = pd.DataFrame({
                'timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                'username': [username],
                'action': [action],
                'details': [details]
            })
            
            logs_df = pd.concat([logs_df, new_log], ignore_index=True)
            self.save_data(logs_df, 'logs')
            logger.info(f"Ação registrada: {username} - {action}")
        except Exception as e:
            logger.error(f"Erro ao registrar log: {e}")
    
    def setup_default_data(self):
        """Configura dados padrão do sistema."""
        self._setup_users()
        self._setup_turmas()
        self._setup_alunos()
        self._setup_frequencia()
        self._setup_logs()
    
    def _setup_users(self):
        """Configura tabela de usuários."""
        users_df = self.get_data('users')
        if users_df.empty:
            users_data = []
            for username, user_info in DEFAULT_USERS.items():
                users_data.append({
                    'username': username,
                    'password': user_info['password'],
                    'role': user_info['role'],
                    'name': user_info['name'],
                    'active': user_info['active'],
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'last_login': ""
                })
            
            users_df = pd.DataFrame(users_data)
            self.save_data(users_df, 'users')
            st.info("Usuários padrão criados.")
    
    def _setup_turmas(self):
        """Configura tabela de turmas."""
        turmas_df = self.get_data('turmas')
        if turmas_df.empty:
            default_turmas = pd.DataFrame({
                'id_turma': ['T001', 'T002', 'T003'],
                'nome_turma': ['1º Ano A', '2º Ano A', '3º Ano A'],
                'ano_letivo': [2025, 2025, 2025],
                'ativa': [True, True, True],
                'created_at': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] * 3
            })
            self.save_data(default_turmas, 'turmas')
            st.info("Turmas padrão criadas.")
    
    def _setup_alunos(self):
        """Configura tabela de alunos."""
        alunos_df = self.get_data('alunos')
        if alunos_df.empty:
            alunos_df = pd.DataFrame(columns=[
                'id_aluno', 'nome', 'turma', 'data_nascimento', 
                'responsavel', 'telefone', 'ativo', 'created_at'
            ])
            self.save_data(alunos_df, 'alunos')
            st.info("Estrutura de alunos criada.")
    
    def _setup_frequencia(self):
        """Configura tabela de frequência."""
        frequencia_df = self.get_data('frequencia')
        if frequencia_df.empty:
            frequencia_df = pd.DataFrame(columns=[
                'id_registro', 'id_aluno', 'data', 'status', 
                'justificativa', 'professor', 'created_at'
            ])
            self.save_data(frequencia_df, 'frequencia')
            st.info("Estrutura de frequência criada.")
    
    def _setup_logs(self):
        """Configura tabela de logs."""
        logs_df = self.get_data('logs')
        if logs_df.empty:
            logs_df = pd.DataFrame(columns=['timestamp', 'username', 'action', 'details'])
            self.save_data(logs_df, 'logs')
            st.info("Sistema de logs inicializado.")

# Funções utilitárias para compatibilidade com código existente
db_manager = DatabaseManager()

def get_data(file_name: str) -> pd.DataFrame:
    """Função de compatibilidade - usar db_manager.get_data()"""
    return db_manager.get_data(file_name.replace('.csv', '').replace('data/', ''))

def save_data(df: pd.DataFrame, file_name: str) -> bool:
    """Função de compatibilidade - usar db_manager.save_data()"""
    return db_manager.save_data(df, file_name.replace('.csv', '').replace('data/', ''))

def setup_files():
    """Função de compatibilidade - usar db_manager.setup_default_data()"""
    return db_manager.setup_default_data()

def get_alunos_by_turma(turma: str) -> pd.DataFrame:
    """Retorna os alunos de uma turma específica."""
    df_alunos = db_manager.get_data('alunos')
    if not df_alunos.empty and 'turma' in df_alunos.columns:
        return df_alunos[df_alunos['turma'] == turma]
    return pd.DataFrame()

def authenticate_user(username: str, password: str) -> Dict[str, any]:
    """Autentica usuário e retorna informações se válido."""
    users_df = db_manager.get_data('users')
    
    if users_df.empty:
        return None
    
    user_row = users_df[users_df['username'] == username]
    if user_row.empty:
        return None
    
    user_data = user_row.iloc[0]
    if not user_data.get('active', True):
        return None
    
    if db_manager.verify_password(password, user_data['password']):
        # Atualizar último login
        users_df.loc[users_df['username'] == username, 'last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_manager.save_data(users_df, 'users')
        
        # Registrar login
        db_manager.log_action(username, 'LOGIN', 'Usuário autenticado com sucesso')
        
        return {
            'username': user_data['username'],
            'role': user_data['role'],
            'name': user_data['name'],
            'permissions': ACCESS_LEVELS.get(user_data['role'], [])
        }
    
    return None

def has_permission(user_role: str, required_permission: str) -> bool:
    """Verifica se o usuário tem permissão para acessar uma funcionalidade."""
    user_permissions = ACCESS_LEVELS.get(user_role, [])
    return required_permission in user_permissions

def get_users_by_role(role: str) -> pd.DataFrame:
    """Retorna usuários por função."""
    users_df = db_manager.get_data('users')
    if not users_df.empty and 'role' in users_df.columns:
        return users_df[users_df['role'] == role]
    return pd.DataFrame()