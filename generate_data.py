import pandas as pd
from datetime import date, timedelta

def generate_frequencia_data():
    """Generates a CSV file of frequency with simulated data."""
    try:
        # Read the CSV with the correct encoding.
        # Add 'skipinitialspace=True' to ignore any leading whitespace in the header.
        df_alunos = pd.read_csv('data/alunos.csv', encoding='utf-8', skipinitialspace=True)
    except UnicodeDecodeError:
        # Fallback to Latin1 if UTF-8 fails
        df_alunos = pd.read_csv('data/alunos.csv', encoding='latin1', skipinitialspace=True)
    
    print("Columns read by pandas:")
    print(df_alunos.columns)
    
    # Check if the 'id_aluno' column exists
    if 'id_aluno' not in df_alunos.columns:
        print("Error: The 'id_aluno' column was not found. Please check your CSV file header.")
        return

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
    print("frequencia.csv file generated with data from July to December 2025.")

if __name__ == '__main__':
    generate_frequencia_data()