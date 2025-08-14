import streamlit as st
import pandas as pd
from datetime import date
from utils.database import get_data, save_data, get_alunos_by_turma, FREQUENCIA_FILE, TURMAS_FILE

if st.session_state.get("role") != "professor":
    st.warning("Você não tem permissão para acessar esta página.")
    st.stop()

st.title("Dashboard do Professor")
st.subheader("Registrar Frequência")

df_turmas = get_data(TURMAS_FILE)
turmas = df_turmas['nome_turma'].tolist()

if not turmas:
    st.warning("Nenhuma turma cadastrada. Contate o administrador.")
    st.stop()

turma_selecionada = st.selectbox("Selecione a Turma:", turmas)
data_selecionada = st.date_input("Selecione a Data:", date.today())

df_alunos = get_alunos_by_turma(turma_selecionada)

if df_alunos.empty:
    st.warning("Nenhum aluno nesta turma.")
else:
    # Cria um formulário para o registro de frequência
    with st.form("form_frequencia"):
        st.write("Marque a frequência dos alunos:")
        
        # DataFrame para armazenar os registros
        registros = []
        
        for _, aluno in df_alunos.iterrows():
            col1, col2, col3 = st.columns([2, 1, 3])
            
            with col1:
                st.write(aluno['nome'])
            
            with col2:
                status = st.radio(" ", ["Presença", "Falta"], key=f"status_{aluno['id_aluno']}", horizontal=True, label_visibility="collapsed")
            
            with col3:
                justificativa = "nda"
                if status == "Falta":
                    justificativa = st.selectbox(
                        "Justificativa",
                        ["nda", "doença", "dificuldade com transporte"],
                        key=f"just_{aluno['id_aluno']}",
                        label_visibility="collapsed"
                    )
            
            registros.append({
                "id_aluno": aluno['id_aluno'],
                "data": data_selecionada,
                "status": status,
                "justificativa": justificativa,
                "professor": st.session_state["username"]
            })
        
        submitted = st.form_submit_button("Salvar Frequência")
        
        if submitted:
            df_frequencia = get_data(FREQUENCIA_FILE)
            for registro in registros:
                novo_registro_df = pd.DataFrame([registro])
                df_frequencia = pd.concat([df_frequencia, novo_registro_df], ignore_index=True)
            
            save_data(df_frequencia, FREQUENCIA_FILE)
            st.success("Frequência salva com sucesso!")