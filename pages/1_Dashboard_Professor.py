import streamlit as st
import pandas as pd
from datetime import date
from utils.database import get_data, save_data, get_alunos_by_turma, FREQUENCIA_FILE, TURMAS_FILE, ALUNOS_FILE

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
    df_frequencia = get_data(FREQUENCIA_FILE)
    
    # Adiciona a coluna 'turma' ao DataFrame de frequência para o filtro funcionar
    df_alunos_completo = get_data(ALUNOS_FILE)
    df_frequencia = pd.merge(df_frequencia, df_alunos_completo[['id_aluno', 'turma']], on='id_aluno', how='left')
    
    # Converte a coluna de data para datetime para permitir a comparação
    if not df_frequencia.empty:
        df_frequencia['data'] = pd.to_datetime(df_frequencia['data']).dt.date
    
    # Verifica se já existe um registro para a turma e data selecionadas
    registros_existentes = df_frequencia[
        (df_frequencia['turma'] == turma_selecionada) & 
        (df_frequencia['data'] == data_selecionada)
    ]
    
    if not registros_existentes.empty:
        st.info("Já existe um registro de frequência para esta turma e data. Você pode alterá-lo e salvar novamente.")
        registros_salvos = registros_existentes.set_index('id_aluno')
    else:
        registros_salvos = pd.DataFrame()

    with st.form("form_frequencia"):
        st.write("Marque a frequência dos alunos:")
        
        registros_a_salvar = []
        
        for _, aluno in df_alunos.iterrows():
            col1, col2, col3 = st.columns([2, 1, 3])
            
            with col1:
                st.write(aluno['nome'])
            
            with col2:
                status_salvo = registros_salvos.loc[aluno['id_aluno'], 'status'] if aluno['id_aluno'] in registros_salvos.index else "Presença"
                status = st.radio(
                    " ",
                    ["Presença", "Falta"],
                    index=0 if status_salvo == "Presença" else 1,
                    key=f"status_{aluno['id_aluno']}",
                    horizontal=True,
                    label_visibility="collapsed"
                )
            
            with col3:
                justificativa = "nda"
                if status == "Falta":
                    justificativa_salva = registros_salvos.loc[aluno['id_aluno'], 'justificativa'] if aluno['id_aluno'] in registros_salvos.index else "nda"
                    opcoes_just = ["nda", "doença", "dificuldade com transporte"]
                    justificativa = st.selectbox(
                        "Justificativa",
                        opcoes_just,
                        index=opcoes_just.index(justificativa_salva),
                        key=f"just_{aluno['id_aluno']}",
                        label_visibility="collapsed"
                    )
            
            registros_a_salvar.append({
                "id_aluno": aluno['id_aluno'],
                "data": data_selecionada,
                "status": status,
                "justificativa": justificativa,
                "professor": st.session_state["username"]
            })
        
        submitted = st.form_submit_button("Salvar Frequência")
        
        if submitted:
            # Releitura para garantir que não haja conflitos de dados
            df_frequencia_atualizado = get_data(FREQUENCIA_FILE)
            if not df_frequencia_atualizado.empty:
                df_frequencia_atualizado['data'] = pd.to_datetime(df_frequencia_atualizado['data']).dt.date
            
            # Filtra os registros a serem removidos, usando a nova coluna 'turma'
            df_frequencia_atualizado = pd.merge(df_frequencia_atualizado, df_alunos_completo[['id_aluno', 'turma']], on='id_aluno', how='left')
            
            # Remove os registros antigos para a turma e data selecionadas
            index_to_drop = df_frequencia_atualizado[
                (df_frequencia_atualizado['turma'] == turma_selecionada) & 
                (df_frequencia_atualizado['data'] == data_selecionada)
            ].index
            df_frequencia_atualizado = df_frequencia_atualizado.drop(index_to_drop)

            # Prepara os novos registros
            novo_registro_df = pd.DataFrame(registros_a_salvar)
            
            # Adiciona os novos registros
            df_frequencia_atualizado = pd.concat([df_frequencia_atualizado, novo_registro_df], ignore_index=True)
            
            # Salva o DataFrame atualizado
            save_data(df_frequencia_atualizado.drop(columns=['turma']), FREQUENCIA_FILE)
            st.success("Frequência salva/atualizada com sucesso!")
            st.rerun()