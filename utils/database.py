import pandas as pd
import os

# Define os caminhos dos arquivos
ALUNOS_FILE = "data/alunos.csv"
TURMAS_FILE = "data/turmas.csv"
FREQUENCIA_FILE = "data/frequencia.csv"

# Verifica se os arquivos existem, se não, os cria
def setup_files():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(ALUNOS_FILE):
        df_alunos = pd.DataFrame(columns=['id_aluno', 'nome', 'turma'])
        df_alunos.to_csv(ALUNos_FILE, index=False)
    if not os.path.exists(TURMAS_FILE):
        df_turmas = pd.DataFrame(columns=['id_turma', 'nome_turma'])
        df_turmas.to_csv(TURMAS_FILE, index=False)
    if not os.path.exists(FREQUENCIA_FILE):
        df_frequencia = pd.DataFrame(columns=['id_aluno', 'data', 'status', 'justificativa', 'professor'])
        df_frequencia.to_csv(FREQUENCIA_FILE, index=False)

def get_data(file_path):
    """Lê um arquivo CSV e retorna um DataFrame."""
    # Garante que a leitura use a codificação correta para o português
    try:
        return pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding='latin1')

def save_data(df, file_path):
    """Salva um DataFrame em um arquivo CSV."""
    df.to_csv(file_path, index=False, encoding='utf-8')


def get_alunos_by_turma(turma):
    """Retorna a lista de alunos de uma turma específica."""
    df_alunos = get_data(ALUNOS_FILE)
    return df_alunos[df_alunos['turma'] == turma]

# Exemplo de dados para simular o login
USERS = {
    "Janecleide": {"password": "jane123", "role": "professor"},
    "Daniele": {"password": "daniele123", "role": "professor"},
    "Lucas": {"password": "lucaslemos123", "role": "professor"},
    "admin": {"password": "admin", "role": "admin"},
    "deangelis": {"password": "bae2025", "role": "coordenador"},
    "Crislania": {"password": "cris123", "role": "agente"}
}