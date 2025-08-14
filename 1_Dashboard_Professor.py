import streamlit as st
import pandas as pd
from datetime import date, timedelta
from utils.database import get_data, save_data, get_alunos_by_turma, FREQUENCIA_FILE, TURMAS_FILE, ALUNOS_FILE

if st.session_state.get("role") != "professor":
    st.warning("Você não tem permissão para acessar esta página.")
    st.stop()

st.title("Dashboard do Professor")

df_turmas = get_data(TURMAS_FILE)
turmas = df_turmas['nome_turma'].tolist()

if not turmas:
    st.warning("Nenhuma turma cadastrada. Contate o administrador.")
    st.stop()

turma_selecionada = st.selectbox("Selecione a Turma:", turmas)
df_alunos = get_alunos_by_turma(turma_selecionada)

# Carrega e mescla os dados para que a coluna 'turma' esteja disponível globalmente no script
df_frequencia = get_data(FREQUENCIA_FILE)
df_alunos_completo = get_data(ALUNOS_FILE)
df_frequencia_com_turma = pd.merge(df_frequencia, df_alunos_completo[['id_aluno', 'turma']], on='id_aluno', how='left')
df_frequencia_com_turma['data'] = pd.to_datetime(df_frequencia_com_turma['data'])

# --- Panorama dos dias de frequência por mês ---
st.subheader("1. Panorama da Frequência por Mês")

# Seletor de Mês
if not df_frequencia_com_turma.empty:
    df_frequencia_com_turma['mes'] = df_frequencia_com_turma['data'].dt.strftime('%Y-%m')
    meses_disponiveis = sorted(df_frequencia_com_turma['mes'].unique(), reverse=True)
else:
    meses_disponiveis = [date.today().strftime('%Y-%m')]

mes_selecionado = st.selectbox("Selecione o Mês:", meses_disponiveis)

# Lógica do Calendário
primeiro_dia_mes_selecionado = pd.to_datetime(f"{mes_selecionado}-01").date()
# Calcula o último dia do mês selecionado
proximo_mes = (primeiro_dia_mes_selecionado + timedelta(days=32)).replace(day=1)
ultimo_dia_mes_selecionado = proximo_mes - timedelta(days=1)

# Filtra a frequência do mês selecionado para a turma selecionada
frequencia_do_mes = df_frequencia_com_turma[
    (df_frequencia_com_turma['data'].dt.date >= primeiro_dia_mes_selecionado) &
    (df_frequencia_com_turma['data'].dt.date <= ultimo_dia_mes_selecionado) &
    (df_frequencia_com_turma['turma'] == turma_selecionada)
]

dias_salvos = frequencia_do_mes['data'].dt.date.unique()
dias_salvos_str = [d.strftime('%Y-%m-%d') for d in dias_salvos]

st.markdown(f"**Mês de {pd.to_datetime(mes_selecionado).strftime('%B de %Y')}**")
dias_da_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
colunas_dias = st.columns(7)
for col, dia_semana in zip(colunas_dias, dias_da_semana):
    col.markdown(f"**{dia_semana}**")

dia_atual = primeiro_dia_mes_selecionado
primeiro_dia_semana = primeiro_dia_mes_selecionado.weekday()
semana_cols = st.columns(7)
for i in range(primeiro_dia_semana):
    semana_cols[i].write("") # Espaços vazios para alinhamento

i = primeiro_dia_semana
while dia_atual <= ultimo_dia_mes_selecionado:
    if i % 7 == 0:
        semana_cols = st.columns(7)

    col = semana_cols[i % 7]
    if dia_atual.weekday() < 5: # Considera apenas dias úteis
        if str(dia_atual) in dias_salvos_str:
            col.button(f"✅ {dia_atual.day}", key=f"btn_{dia_atual}", disabled=True)
        else:
            col.button(f"⬜ {dia_atual.day}", key=f"btn_{dia_atual}", disabled=True)
    
    dia_atual += timedelta(days=1)
    i += 1

data_selecionada = st.date_input("Selecione uma data para registrar a frequência:", date.today())


# --- Registrar/Refazer Frequência ---
st.subheader("2. Registrar/Refazer Frequência")
if df_alunos.empty:
    st.warning("Nenhum aluno nesta turma.")
else:
    # A mesclagem já foi feita no início do script
    df_frequencia_com_turma['data'] = df_frequencia_com_turma['data'].dt.date
    
    registros_existentes = df_frequencia_com_turma[
        (df_frequencia_com_turma['turma'] == turma_selecionada) & 
        (df_frequencia_com_turma['data'] == data_selecionada)
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
                        index=opcoes_just.index(justificativa_salva) if justificativa_salva in opcoes_just else 0,
                        key=f"just_{aluno['id_aluno']}",
                        label_visibility="collapsed"
                    )
            
            registros_a_salvar.append({
                "id_aluno": aluno['id_aluno'],
                "data": data_selecionada,
                "status": status,
                "justificativa": justificativa,
                "professor": st.session_state["username"],
            })
        
        submitted = st.form_submit_button("Salvar Frequência")
        
        if submitted:
            df_frequencia_atualizado = get_data(FREQUENCIA_FILE)
            df_frequencia_atualizado = pd.merge(df_frequencia_atualizado, df_alunos_completo[['id_aluno', 'turma']], on='id_aluno', how='left')
            df_frequencia_atualizado['data'] = pd.to_datetime(df_frequencia_atualizado['data']).dt.date
            
            index_to_drop = df_frequencia_atualizado[
                (df_frequencia_atualizado['turma'] == turma_selecionada) & 
                (df_frequencia_atualizado['data'] == data_selecionada)
            ].index
            df_frequencia_atualizado = df_frequencia_atualizado.drop(index_to_drop)

            novo_registro_df = pd.DataFrame(registros_a_salvar)
            
            df_frequencia_atualizado = pd.concat([df_frequencia_atualizado, novo_registro_df], ignore_index=True)
            
            save_data(df_frequencia_atualizado.drop(columns=['turma']), FREQUENCIA_FILE)
            st.success("Frequência salva/atualizada com sucesso!")
            st.rerun()