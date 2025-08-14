import streamlit as st
import pandas as pd
from io import BytesIO
from utils.database import get_data, FREQUENCIA_FILE, ALUNOS_FILE, TURMAS_FILE
import plotly.express as px

if st.session_state.get("role") != "agente":
    st.warning("Você não tem permissão para acessar esta página.")
    st.stop()

st.title("Dashboard do Agente")

df_frequencia = get_data(FREQUENCIA_FILE)
df_alunos = get_data(ALUNOS_FILE)
df_turmas = get_data(TURMAS_FILE)

# --- Download da Tabela de Frequência ---
st.subheader("Download da Tabela de Frequência")

if not df_frequencia.empty:
    meses = sorted(df_frequencia['data'].apply(lambda x: pd.to_datetime(x).strftime('%Y-%m')).unique())
    turmas = df_turmas['nome_turma'].tolist()
    
    col1, col2 = st.columns(2)
    with col1:
        mes_selecionado = st.selectbox("Selecione o Mês:", meses)
    with col2:
        turma_selecionada = st.selectbox("Selecione a Turma:", turmas)
    
    df_frequencia['data'] = pd.to_datetime(df_frequencia['data'])
    df_filtrado = df_frequencia[df_frequencia['data'].dt.strftime('%Y-%m') == mes_selecionado]
    
    df_alunos_filtrado = df_alunos[df_alunos['turma'] == turma_selecionada]
    
    df_download = pd.merge(df_alunos_filtrado, df_filtrado, on='id_aluno', how='left')
    
    def to_excel(df):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Frequencia')
        writer.close()
        processed_data = output.getvalue()
        return processed_data

    excel_data = to_excel(df_download)
    st.download_button(
        label="Baixar Tabela de Frequência (Excel)",
        data=excel_data,
        file_name=f"frequencia_{turma_selecionada}_{mes_selecionado}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- Analytics de Frequência ---
st.subheader("Analytics de Frequência")

if not df_frequencia.empty:
    frequencia_alunos = df_frequencia.groupby('id_aluno')['status'].value_counts().unstack(fill_value=0)
    frequencia_alunos['total'] = frequencia_alunos.sum(axis=1)
    frequencia_alunos['%_presenca'] = (frequencia_alunos['Presença'] / frequencia_alunos['total']) * 100
    
    df_analytics = pd.merge(df_alunos, frequencia_alunos, on='id_aluno')
    df_analytics = df_analytics.sort_values(by='%_presenca', ascending=True)

    fig = px.bar(
        df_analytics,
        x='nome',
        y='%_presenca',
        title="Percentual de Presença por Aluno",
        color='%_presenca'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Justificativas de Falta")
    justificativas = df_frequencia[df_frequencia['status'] == 'Falta']['justificativa'].value_counts()
    fig_pie = px.pie(
        justificativas,
        values=justificativas.values,
        names=justificativas.index,
        title="Distribuição das Justificativas de Falta"
    )
    st.plotly_chart(fig_pie)
else:
    st.warning("Nenhum dado de frequência para análise.")