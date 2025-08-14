import streamlit as st
import pandas as pd
from utils.database import get_data, FREQUENCIA_FILE, TURMAS_FILE, ALUNOS_FILE
import plotly.express as px
from fpdf import FPDF
from io import BytesIO

# Verificação de permissão
if st.session_state.get("role") != "coordenador":
    st.warning("Você não tem permissão para acessar esta página.")
    st.stop()

st.title("Dashboard do Coordenador")

# Carrega os dados
df_frequencia = get_data(FREQUENCIA_FILE)
df_turmas = get_data(TURMAS_FILE)
df_alunos = get_data(ALUNOS_FILE)

# Processamento de dados
if not df_frequencia.empty:
    df_frequencia['data'] = pd.to_datetime(df_frequencia['data'])
    df_frequencia = pd.merge(df_frequencia, df_alunos[['id_aluno', 'nome', 'turma']], on='id_aluno')

# ---
### 1. Registros Mais Recentes

st.header("1. Registros Mais Recentes")
if not df_frequencia.empty:
    st.dataframe(
        df_frequencia[['data', 'nome', 'turma', 'status', 'justificativa', 'professor']]
        .sort_values(by='data', ascending=False)
        .head(10),
        use_container_width=True
    )
else:
    st.info("Nenhum registro de frequência encontrado.")

# ---
### 2. Acompanhamento de Frequência Geral

st.header("2. Acompanhamento de Frequência Geral")
if not df_frequencia.empty:
    # Gráfico de Frequência por Status
    contagem_status = df_frequencia['status'].value_counts().reset_index()
    contagem_status.columns = ['Status', 'Total']
    fig_status = px.pie(
        contagem_status,
        names='Status',
        values='Total',
        title='Frequência Total (Presença vs. Falta)',
        color_discrete_map={'Presença': '#00b33c', 'Falta': '#ff3300'}
    )
    st.plotly_chart(fig_status, use_container_width=True)

    # Gráfico de Frequência por Turma
    frequencia_por_turma = df_frequencia.groupby(['turma', 'status']).size().reset_index(name='contagem')
    fig_turma = px.bar(
        frequencia_por_turma,
        x='turma',
        y='contagem',
        color='status',
        barmode='group',
        title='Frequência por Turma',
        color_discrete_map={'Presença': '#00b33c', 'Falta': '#ff3300'}
    )
    st.plotly_chart(fig_turma, use_container_width=True)
else:
    st.info("Nenhum dado de frequência para análise.")

# ---
### 3. Analytics de Faltas

st.header("3. Analytics de Faltas")
if not df_frequencia.empty:
    # Alunos com maior percentual de faltas
    faltas_por_aluno = df_frequencia.groupby('id_aluno')['status'].apply(
        lambda x: (x == 'Falta').sum() / x.count()
    ).reset_index(name='percentual_faltas')
    
    alunos_com_faltas = pd.merge(faltas_por_aluno, df_alunos[['id_aluno', 'nome', 'turma']], on='id_aluno')
    alunos_com_faltas = alunos_com_faltas[alunos_com_faltas['percentual_faltas'] > 0]
    alunos_com_faltas = alunos_com_faltas.sort_values(by='percentual_faltas', ascending=False).head(10)
    
    st.subheader("Top 10 Alunos com Maior Percentual de Faltas")
    st.dataframe(alunos_com_faltas[['nome', 'turma', 'percentual_faltas']].style.format({'percentual_faltas': '{:.2%}'}), use_container_width=True)
    
    # Percentual de faltas por turma
    faltas_por_turma = df_frequencia.groupby('turma')['status'].apply(
        lambda x: (x == 'Falta').sum() / x.count()
    ).reset_index(name='percentual_faltas')
    
    st.subheader("Percentual de Faltas por Turma")
    st.dataframe(faltas_por_turma.style.format({'percentual_faltas': '{:.2%}'}), use_container_width=True)
else:
    st.info("Nenhum dado de frequência para análise.")

# ---
### 4. Download de Relatório de Ocorrências (PDF)

st.header("4. Relatório de Ocorrências Mensais")
if not df_frequencia.empty:
    # Selecionar o mês
    df_frequencia['mes'] = df_frequencia['data'].dt.strftime('%Y-%m')
    meses_disponiveis = sorted(df_frequencia['mes'].unique())
    mes_selecionado = st.selectbox("Selecione o Mês para o Relatório:", meses_disponiveis)

    # Função para gerar o PDF
    def gerar_pdf(mes, df_relatorio):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, f"Relatório de Ocorrências - {mes}", 0, 1, 'C')

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(40, 10, "Data", 1)
        pdf.cell(70, 10, "Aluno", 1)
        pdf.cell(20, 10, "Status", 1)
        pdf.cell(60, 10, "Justificativa", 1)
        pdf.ln()

        pdf.set_font("Arial", '', 10)
        for _, row in df_relatorio.iterrows():
            pdf.cell(40, 10, str(row['data'].strftime('%Y-%m-%d')), 1)
            pdf.cell(70, 10, str(row['nome']), 1)
            pdf.cell(20, 10, str(row['status']), 1)
            pdf.cell(60, 10, str(row['justificativa']), 1)
            pdf.ln()
            
        return pdf

    # Filtra o DataFrame para o mês selecionado
    df_relatorio = df_frequencia[(df_frequencia['mes'] == mes_selecionado) & (df_frequencia['status'] == 'Falta')]
    
    if not df_relatorio.empty:
        pdf_relatorio = gerar_pdf(mes_selecionado, df_relatorio)
        pdf_output = BytesIO(pdf_relatorio.output(dest='S'))

        st.download_button(
            label="Baixar Relatório de Ocorrências (PDF)",
            data=pdf_output,
            file_name=f"relatorio_ocorrencias_{mes_selecionado}.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Nenhuma ocorrência de falta registrada neste mês.")
else:
    st.info("Nenhum dado de frequência para gerar o relatório.")