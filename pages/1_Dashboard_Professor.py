import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar
from utils.database import get_data, save_data, get_alunos_by_turma, FREQUENCIA_FILE, TURMAS_FILE, ALUNOS_FILE

# Configuração da página
st.set_page_config(
    page_title="Dashboard do Professor",
    page_icon="👨‍🏫",
    layout="wide"
)

# Verificação de permissão
if st.session_state.get("role") != "professor":
    st.error("🚫 Você não tem permissão para acessar esta página.")
    st.stop()

# CSS customizado para melhor visualização
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .attendance-summary {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    
    .day-present {
        background: #28a745;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px;
        margin: 2px;
        font-size: 12px;
        width: 100%;
    }
    
    .day-absent {
        background: #dc3545;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px;
        margin: 2px;
        font-size: 12px;
        width: 100%;
    }
    
    .day-empty {
        background: #e9ecef;
        color: #6c757d;
        border: 1px dashed #ced4da;
        border-radius: 5px;
        padding: 5px;
        margin: 2px;
        font-size: 12px;
        width: 100%;
    }
    
    .student-row {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 5px;
        border: 1px solid #dee2e6;
    }
    
    .student-row:hover {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.title("👨‍🏫 Dashboard do Professor")

# Carregamento de dados
@st.cache_data
def load_data():
    df_turmas = get_data(TURMAS_FILE)
    df_alunos_completo = get_data(ALUNOS_FILE)
    df_frequencia = get_data(FREQUENCIA_FILE)
    
    if not df_frequencia.empty:
        df_frequencia_com_turma = pd.merge(
            df_frequencia, 
            df_alunos_completo[['id_aluno', 'turma']], 
            on='id_aluno', 
            how='left'
        )
        df_frequencia_com_turma['data'] = pd.to_datetime(df_frequencia_com_turma['data'])
    else:
        df_frequencia_com_turma = pd.DataFrame()
    
    return df_turmas, df_alunos_completo, df_frequencia_com_turma

df_turmas, df_alunos_completo, df_frequencia_com_turma = load_data()
turmas = df_turmas['nome_turma'].tolist()

if not turmas:
    st.warning("⚠️ Nenhuma turma cadastrada. Contate o administrador.")
    st.stop()

# Seleção de turma
col1, col2 = st.columns([2, 1])
with col1:
    turma_selecionada = st.selectbox("🏫 Selecione a Turma:", turmas, key="turma_select")

df_alunos = get_alunos_by_turma(turma_selecionada)

# Métricas da turma
with col2:
    if not df_alunos.empty:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{len(df_alunos)}</h3>
            <p>Alunos na Turma</p>
        </div>
        """, unsafe_allow_html=True)

# Tabs para organizar o conteúdo
tab1, tab2, tab3 = st.tabs(["📅 Calendário de Frequência", "📊 Registrar Frequência", "📈 Relatórios"])

with tab1:
    st.subheader("📅 Calendário de Frequência")
    
    # Seletor de mês
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if not df_frequencia_com_turma.empty:
            df_frequencia_com_turma['mes'] = df_frequencia_com_turma['data'].dt.strftime('%Y-%m')
            meses_disponiveis = sorted(df_frequencia_com_turma['mes'].unique(), reverse=True)
        else:
            meses_disponiveis = [date.today().strftime('%Y-%m')]
        
        mes_selecionado = st.selectbox("📆 Selecione o Mês:", meses_disponiveis, key="mes_select")
    
    # Cálculo do calendário
    primeiro_dia_mes = pd.to_datetime(f"{mes_selecionado}-01").date()
    proximo_mes = (primeiro_dia_mes + timedelta(days=32)).replace(day=1)
    ultimo_dia_mes = proximo_mes - timedelta(days=1)
    
    # Filtrar frequência do mês
    frequencia_do_mes = df_frequencia_com_turma[
        (df_frequencia_com_turma['data'].dt.date >= primeiro_dia_mes) &
        (df_frequencia_com_turma['data'].dt.date <= ultimo_dia_mes) &
        (df_frequencia_com_turma['turma'] == turma_selecionada)
    ] if not df_frequencia_com_turma.empty else pd.DataFrame()
    
    # Estatísticas do mês
    if not frequencia_do_mes.empty:
        dias_com_registro = len(frequencia_do_mes['data'].dt.date.unique())
        total_presencas = len(frequencia_do_mes[frequencia_do_mes['status'] == 'Presença'])
        total_faltas = len(frequencia_do_mes[frequencia_do_mes['status'] == 'Falta'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📅 Dias Registrados", dias_com_registro)
        with col2:
            st.metric("✅ Total Presenças", total_presencas)
        with col3:
            st.metric("❌ Total Faltas", total_faltas)
        with col4:
            taxa_presenca = (total_presencas / (total_presencas + total_faltas) * 100) if (total_presencas + total_faltas) > 0 else 0
            st.metric("📊 Taxa Presença", f"{taxa_presenca:.1f}%")
    
    # Calendário visual
    st.markdown(f"### {calendar.month_name[primeiro_dia_mes.month]} {primeiro_dia_mes.year}")
    
    dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    cols_header = st.columns(7)
    for col, dia in zip(cols_header, dias_semana):
        col.markdown(f"**{dia[:3]}**")
    
    # Construir calendário
    cal = calendar.monthcalendar(primeiro_dia_mes.year, primeiro_dia_mes.month)
    
    for semana in cal:
        cols_semana = st.columns(7)
        for i, dia in enumerate(semana):
            if dia == 0:
                cols_semana[i].write("")
            else:
                data_dia = date(primeiro_dia_mes.year, primeiro_dia_mes.month, dia)
                
                # Verificar se há registro para este dia
                registros_dia = frequencia_do_mes[
                    frequencia_do_mes['data'].dt.date == data_dia
                ] if not frequencia_do_mes.empty else pd.DataFrame()
                
                if not registros_dia.empty:
                    presencas = len(registros_dia[registros_dia['status'] == 'Presença'])
                    faltas = len(registros_dia[registros_dia['status'] == 'Falta'])
                    
                    if presencas > faltas:
                        status_class = "day-present"
                        icon = "✅"
                    else:
                        status_class = "day-absent"
                        icon = "❌"
                    
                    if cols_semana[i].button(
                        f"{icon} {dia}\n({presencas}P/{faltas}F)", 
                        key=f"cal_{data_dia}",
                        help=f"Dia {dia}: {presencas} presenças, {faltas} faltas"
                    ):
                        st.session_state['data_selecionada_calendario'] = data_dia
                        st.rerun()
                else:
                    # Só mostrar dias úteis (seg-sex) como disponíveis
                    if data_dia.weekday() < 5 and data_dia <= date.today():
                        cols_semana[i].button(
                            f"⬜ {dia}", 
                            key=f"cal_empty_{data_dia}",
                            help=f"Sem registro para {data_dia}"
                        )
                    else:
                        cols_semana[i].write(f"{dia}")

with tab2:
    st.subheader("📊 Registrar/Editar Frequência")
    
    # Seleção de data
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Usar data do calendário se foi selecionada
        data_inicial = st.session_state.get('data_selecionada_calendario', date.today())
        data_selecionada = st.date_input(
            "📅 Selecione a data:", 
            value=data_inicial,
            key="data_frequencia"
        )
    
    with col2:
        # Mostrar informações da data selecionada
        if not df_frequencia_com_turma.empty:
            registros_data = df_frequencia_com_turma[
                (df_frequencia_com_turma['turma'] == turma_selecionada) & 
                (df_frequencia_com_turma['data'].dt.date == data_selecionada)
            ]
            
            if not registros_data.empty:
                presencas = len(registros_data[registros_data['status'] == 'Presença'])
                faltas = len(registros_data[registros_data['status'] == 'Falta'])
                st.info(f"✅ {presencas} presenças | ❌ {faltas} faltas")
            else:
                st.warning("📝 Sem registro para esta data")
    
    if df_alunos.empty:
        st.warning("⚠️ Nenhum aluno nesta turma.")
    else:
        # Buscar registros existentes
        df_frequencia_atual = get_data(FREQUENCIA_FILE)
        if not df_frequencia_atual.empty:
            df_frequencia_com_turma_atual = pd.merge(
                df_frequencia_atual, 
                df_alunos_completo[['id_aluno', 'turma']], 
                on='id_aluno', 
                how='left'
            )
            df_frequencia_com_turma_atual['data'] = pd.to_datetime(df_frequencia_com_turma_atual['data']).dt.date
            
            registros_existentes = df_frequencia_com_turma_atual[
                (df_frequencia_com_turma_atual['turma'] == turma_selecionada) & 
                (df_frequencia_com_turma_atual['data'] == data_selecionada)
            ]
        else:
            registros_existentes = pd.DataFrame()
        
        if not registros_existentes.empty:
            st.info("✏️ Já existe registro para esta data. Você pode editá-lo abaixo.")
            registros_salvos = registros_existentes.set_index('id_aluno')
        else:
            registros_salvos = pd.DataFrame()
        
        # Formulário de frequência
        with st.form("form_frequencia", clear_on_submit=False):
            st.markdown("### 👥 Lista de Alunos")
            
            # Ações em lote
            col1, col2, col3 = st.columns(3)
            with col1:
                marcar_todos_presente = st.checkbox("✅ Marcar todos como presente")
            with col2:
                marcar_todos_falta = st.checkbox("❌ Marcar todos como falta")
            
            registros_a_salvar = []
            
            # Lista de alunos
            for idx, aluno in df_alunos.iterrows():
                with st.container():
                    st.markdown('<div class="student-row">', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns([3, 2, 3])
                    
                    with col1:
                        st.markdown(f"**👤 {aluno['nome']}**")
                    
                    with col2:
                        # Determinar status atual
                        if marcar_todos_presente:
                            status_default = "Presença"
                        elif marcar_todos_falta:
                            status_default = "Falta"
                        else:
                            status_default = (
                                registros_salvos.loc[aluno['id_aluno'], 'status'] 
                                if aluno['id_aluno'] in registros_salvos.index 
                                else "Presença"
                            )
                        
                        status = st.radio(
                            "Status",
                            ["Presença", "Falta"],
                            index=0 if status_default == "Presença" else 1,
                            key=f"status_{aluno['id_aluno']}_{data_selecionada}",
                            horizontal=True,
                            label_visibility="collapsed"
                        )
                    
                    with col3:
                        justificativa = "nda"
                        if status == "Falta":
                            justificativa_salva = (
                                registros_salvos.loc[aluno['id_aluno'], 'justificativa'] 
                                if aluno['id_aluno'] in registros_salvos.index 
                                else "nda"
                            )
                            opcoes_just = ["nda", "doença", "dificuldade com transporte", "motivo familiar", "outros"]
                            justificativa = st.selectbox(
                                "Justificativa",
                                opcoes_just,
                                index=opcoes_just.index(justificativa_salva) if justificativa_salva in opcoes_just else 0,
                                key=f"just_{aluno['id_aluno']}_{data_selecionada}",
                                label_visibility="collapsed"
                            )
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                registros_a_salvar.append({
                    "id_aluno": aluno['id_aluno'],
                    "data": data_selecionada,
                    "status": status,
                    "justificativa": justificativa,
                    "professor": st.session_state.get("username", "Professor"),
                })
            
            # Resumo antes de salvar
            st.markdown("### 📊 Resumo")
            presencas_count = sum(1 for r in registros_a_salvar if r['status'] == 'Presença')
            faltas_count = sum(1 for r in registros_a_salvar if r['status'] == 'Falta')
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"✅ Presenças: {presencas_count}")
            with col2:
                st.error(f"❌ Faltas: {faltas_count}")
            
            submitted = st.form_submit_button("💾 Salvar Frequência", type="primary", use_container_width=True)
            
            if submitted:
                try:
                    # Recarregar dados atuais
                    df_frequencia_atualizado = get_data(FREQUENCIA_FILE)
                    
                    if not df_frequencia_atualizado.empty:
                        df_frequencia_atualizado = pd.merge(
                            df_frequencia_atualizado, 
                            df_alunos_completo[['id_aluno', 'turma']], 
                            on='id_aluno', 
                            how='left'
                        )
                        df_frequencia_atualizado['data'] = pd.to_datetime(df_frequencia_atualizado['data']).dt.date
                        
                        # Remover registros existentes para esta data/turma
                        index_to_drop = df_frequencia_atualizado[
                            (df_frequencia_atualizado['turma'] == turma_selecionada) & 
                            (df_frequencia_atualizado['data'] == data_selecionada)
                        ].index
                        df_frequencia_atualizado = df_frequencia_atualizado.drop(index_to_drop)
                        df_frequencia_atualizado = df_frequencia_atualizado.drop(columns=['turma'])
                    else:
                        df_frequencia_atualizado = pd.DataFrame()
                    
                    # Adicionar novos registros
                    novo_registro_df = pd.DataFrame(registros_a_salvar)
                    df_frequencia_atualizado = pd.concat([df_frequencia_atualizado, novo_registro_df], ignore_index=True)
                    
                    # Salvar
                    save_data(df_frequencia_atualizado, FREQUENCIA_FILE)
                    
                    # Limpar cache
                    st.cache_data.clear()
                    
                    st.success(f"✅ Frequência salva com sucesso! {presencas_count} presenças e {faltas_count} faltas registradas.")
                    st.balloons()
                    
                    # Pequeno delay para mostrar a mensagem
                    import time
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {str(e)}")

with tab3:
    st.subheader("📈 Relatórios de Frequência")
    
    if not df_frequencia_com_turma.empty:
        # Filtrar por turma
        freq_turma = df_frequencia_com_turma[df_frequencia_com_turma['turma'] == turma_selecionada]
        
        if not freq_turma.empty:
            # Relatório por aluno
            st.markdown("#### 👥 Frequência por Aluno")
            
            relatorio_alunos = []
            for _, aluno in df_alunos.iterrows():
                freq_aluno = freq_turma[freq_turma['id_aluno'] == aluno['id_aluno']]
                if not freq_aluno.empty:
                    total_dias = len(freq_aluno)
                    presencas = len(freq_aluno[freq_aluno['status'] == 'Presença'])
                    faltas = len(freq_aluno[freq_aluno['status'] == 'Falta'])
                    taxa_presenca = (presencas / total_dias * 100) if total_dias > 0 else 0
                    
                    relatorio_alunos.append({
                        'Aluno': aluno['nome'],
                        'Total Dias': total_dias,
                        'Presenças': presencas,
                        'Faltas': faltas,
                        'Taxa Presença (%)': f"{taxa_presenca:.1f}%"
                    })
                else:
                    relatorio_alunos.append({
                        'Aluno': aluno['nome'],
                        'Total Dias': 0,
                        'Presenças': 0,
                        'Faltas': 0,
                        'Taxa Presença (%)': "0.0%"
                    })
            
            df_relatorio = pd.DataFrame(relatorio_alunos)
            st.dataframe(df_relatorio, use_container_width=True)
            
            # Gráfico de frequência mensal
            st.markdown("#### 📊 Frequência Mensal")
            freq_mensal = freq_turma.groupby(freq_turma['data'].dt.to_period('M')).agg({
                'status': lambda x: (x == 'Presença').sum(),
                'id_aluno': 'count'
            }).reset_index()
            
            freq_mensal.columns = ['Mês', 'Presenças', 'Total']
            freq_mensal['Faltas'] = freq_mensal['Total'] - freq_mensal['Presenças']
            freq_mensal['Taxa Presença'] = (freq_mensal['Presenças'] / freq_mensal['Total'] * 100).round(1)
            
            st.dataframe(freq_mensal, use_container_width=True)
            
        else:
            st.info("📝 Nenhum dado de frequência encontrado para esta turma.")
    else:
        st.info("📝 Nenhum dado de frequência encontrado no sistema.")