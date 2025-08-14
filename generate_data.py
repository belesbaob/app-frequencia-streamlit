import pandas as pd
from datetime import date, timedelta

def generate_frequencia_data():
    """Gera um arquivo CSV de frequência com dados simulados."""
    # AQUI ESTÁ A MUDANÇA: use UTF-8 para ler
    df_alunos = pd.read_csv('data/alunos.csv', encoding='utf-8') 
    frequencia_data = []

    start_date = date(2025, 7, 1)
    end_date = date(2025, 12, 31)

    delta = timedelta(days=1)

    while start_date <= end_date:
        if start_date.weekday() < 5:
            for _, aluno in df_alunos.iterrows():
                frequencia_data.append({
                    'id_aluno': aluno['id_aluno'],
                    'data': start_date.strftime('%Y-%m-%d'),
                    'status': 'Presença',
                    'justificativa': 'nda',
                    'professor': 'professor1'
                })
        start_date += delta

    df_frequencia = pd.DataFrame(frequencia_data)
    df_frequencia.to_csv('data/frequencia.csv', index=False, encoding='utf-8')
    print("Arquivo frequencia.csv gerado com dados de julho a dezembro de 2025.")

if __name__ == '__main__':
    generate_frequencia_data()