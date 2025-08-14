import streamlit as st
import pandas as pd
from utils.database import get_data, FREQUENCIA_FILE, TURMAS_FILE, ALUNOS_FILE
import plotly.express as px

# Verificação de permissão
if st.session_state.get("role") != "admin":
    st.warning("Você não tem permissão para acessar esta página.")
    st.stop()

st.title("Dashboard Administrativo")

# Carrega os dados
df_frequencia = get_data(FREQUENCIA_FILE)
df_turmas = get_data(TURMAS_FILE)
df_alunos = get_data(ALUNOS_FILE)

# Processamento de dados
if not df_frequencia.empty:
    df_frequencia['data'] = pd.to_datetime(df_frequencia['data'])
    df_frequencia = pd.merge(df_frequencia, df_alunos[['id_aluno', 'nome', 'turma']], on='id_aluno')

# ---
### 1. Visualização de Turmas e Alunos

st.header("1. Visualização de Turmas e Alunos")
turma_selecionada = st.selectbox(
    "Selecione uma Turma para visualizar os alunos:",
    df_turmas['nome_turma'].unique() if not df_turmas.empty else []
)

if turma_selecionada:
    alunos_na_turma = df_alunos[df_alunos['turma'] == turma_selecionada]
    st.write(f"### Alunos na Turma: {turma_selecionada}")
    st.dataframe(alunos_na_turma[['id_aluno', 'nome']], use_container_width=True)
else:
    st.info("Nenhuma turma encontrada.")

# ---
### 2. Acompanhamento dos Registros dos Professores

st.header("2. Acompanhamento de Registros de Frequência")
if not df_frequencia.empty:
    registros_por_professor = df_frequencia.groupby('professor').size().reset_index(name='total_registros')
    
    st.subheader("Total de Registros por Professor")
    st.dataframe(registros_por_professor, use_container_width=True)
    
    st.subheader("Registros mais recentes")
    st.dataframe(
        df_frequencia[['data', 'nome', 'turma', 'status', 'justificativa', 'professor']]
        .sort_values(by='data', ascending=False)
        .head(10),
        use_container_width=True
    )
else:
    st.info("Nenhum registro de frequência encontrado.")

# ---
### 3. Analytics de Faltas por Turmas e Alunos

st.header("3. Analytics de Faltas")
if not df_frequencia.empty:
    # Percentual de faltas por turma
    faltas_por_turma = df_frequencia.groupby('turma')['status'].apply(
        lambda x: (x == 'Falta').sum() / x.count()
    ).reset_index(name='percentual_faltas')
    
    st.subheader("Percentual de Faltas por Turma")
    fig_faltas_turma = px.bar(
        faltas_por_turma,
        x='turma',
        y='percentual_faltas',
        title='Percentual de Faltas por Turma',
        labels={'turma': 'Turma', 'percentual_faltas': 'Percentual de Faltas'}
    )
    st.plotly_chart(fig_faltas_turma, use_container_width=True)

    # Alunos com maior percentual de faltas
    faltas_por_aluno = df_frequencia.groupby('id_aluno')['status'].apply(
        lambda x: (x == 'Falta').sum() / x.count() if x.count() > 0 else 0
    ).reset_index(name='percentual_faltas')
    
    alunos_com_faltas = pd.merge(faltas_por_aluno, df_alunos[['id_aluno', 'nome', 'turma']], on='id_aluno')
    alunos_com_faltas = alunos_com_faltas.sort_values(by='percentual_faltas', ascending=False).head(10)
    
    st.subheader("Top 10 Alunos com Maior Percentual de Faltas")
    st.dataframe(alunos_com_faltas[['nome', 'turma', 'percentual_faltas']].style.format({'percentual_faltas': '{:.2%}'}), use_container_width=True)
else:
    st.info("Nenhum dado de frequência para análise.")