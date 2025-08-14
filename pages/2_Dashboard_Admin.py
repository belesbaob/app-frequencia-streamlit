import streamlit as st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from utils.database import get_data, save_data, FREQUENCIA_FILE, TURMAS_FILE, ALUNOS_FILE

# Configuração da página
st.set_page_config(
    page_title="Dashboard Administrativo",
    page_icon="👨‍💼",
    layout="wide"
)

# Verificação de permissão
if st.session_state.get("role") != "admin":
    st.error("🚫 Você não tem permissão para acessar esta página.")
    st.stop()

# CSS customizado para interface moderna
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }
    
    .danger-zone {
        background: #fff5f5;
        border: 2px solid #fed7d7;
        border-radius: 10px;
        padding: 2rem;
        margin: 2rem 0;
    }
    
    .success-card {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        padding: 1rem;
        border-radius: 8px;
        color: #2d3748;
        margin: 1rem 0;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1rem;
        border-radius: 8px;
        color: #744210;
        margin: 1rem 0;
    }
    
    .data-table {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .filter-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown("""
<div class="main-header">
    <h1>👨‍💼 Dashboard Administrativo</h1>
    <p>Painel de controle e monitoramento do sistema de frequência</p>
</div>
""", unsafe_allow_html=True)

# Carregamento e cache de dados
@st.cache_data
def load_all_data():
    """Carrega todos os dados com cache para melhor performance"""
    df_frequencia = get_data(FREQUENCIA_FILE)
    df_turmas = get_data(TURMAS_FILE)
    df_alunos = get_data(ALUNOS_FILE)
    
    # Processamento de dados
    if not df_frequencia.empty and not df_alunos.empty:
        df_frequencia['data'] = pd.to_datetime(df_frequencia['data'])
        df_frequencia_completa = pd.merge(
            df_frequencia, 
            df_alunos[['id_aluno', 'nome', 'turma']], 
            on='id_aluno', 
            how='left'
        )
    else:
        df_frequencia_completa = pd.DataFrame()
    
    return df_frequencia, df_turmas, df_alunos, df_frequencia_completa

df_frequencia, df_turmas, df_alunos, df_frequencia_completa = load_all_data()

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_turmas = len(df_turmas) if not df_turmas.empty else 0
    st.markdown(f"""
    <div class="metric-card">
        <h2>🏫 {total_turmas}</h2>
        <p>Turmas Cadastradas</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    total_alunos = len(df_alunos) if not df_alunos.empty else 0
    st.markdown(f"""
    <div class="metric-card">
        <h2>👥 {total_alunos}</h2>
        <p>Alunos Matriculados</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    total_registros = len(df_frequencia) if not df_frequencia.empty else 0
    st.markdown(f"""
    <div class="metric-card">
        <h2>📊 {total_registros}</h2>
        <p>Registros de Frequência</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    professores_ativos = len(df_frequencia['professor'].unique()) if not df_frequencia.empty else 0
    st.markdown(f"""
    <div class="metric-card">
        <h2>👨‍🏫 {professores_ativos}</h2>
        <p>Professores Ativos</p>
    </div>
    """, unsafe_allow_html=True)

# Tabs principais
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏫 Gestão de Turmas", 
    "📊 Analytics Avançadas", 
    "👨‍🏫 Monitoramento Professores", 
    "📈 Relatórios Detalhados",
    "⚙️ Administração"
])

with tab1:
    st.subheader("🏫 Gestão de Turmas e Alunos")
    
    if not df_turmas.empty:
        # Filtros
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1])
        
        with col1:
            turma_selecionada = st.selectbox(
                "📚 Selecione uma Turma:",
                ["Todas as Turmas"] + df_turmas['nome_turma'].tolist(),
                key="turma_gestao"
            )
        
        with col2:
            if turma_selecionada != "Todas as Turmas":
                alunos_na_turma = df_alunos[df_alunos['turma'] == turma_selecionada]
                st.info(f"👥 {len(alunos_na_turma)} alunos")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Visualização de alunos
        if turma_selecionada == "Todas as Turmas":
            st.markdown("### 👥 Todos os Alunos por Turma")
            
            # Resumo por turma
            resumo_turmas = df_alunos.groupby('turma').agg({
                'id_aluno': 'count',
                'nome': lambda x: ', '.join(x[:3]) + ('...' if len(x) > 3 else '')
            }).reset_index()
            resumo_turmas.columns = ['Turma', 'Qtd Alunos', 'Primeiros Alunos']
            
            st.markdown('<div class="data-table">', unsafe_allow_html=True)
            st.dataframe(resumo_turmas, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Gráfico de distribuição
            fig_dist = px.pie(
                resumo_turmas, 
                values='Qtd Alunos', 
                names='Turma',
                title="Distribuição de Alunos por Turma",
                hole=0.4
            )
            fig_dist.update_layout(height=400)
            st.plotly_chart(fig_dist, use_container_width=True)
            
        else:
            st.markdown(f"### 👥 Alunos da Turma: {turma_selecionada}")
            alunos_na_turma = df_alunos[df_alunos['turma'] == turma_selecionada]
            
            if not alunos_na_turma.empty:
                # Adicionar informações de frequência se disponível
                if not df_frequencia_completa.empty:
                    freq_por_aluno = df_frequencia_completa[
                        df_frequencia_completa['turma'] == turma_selecionada
                    ].groupby('id_aluno').agg({
                        'status': ['count', lambda x: (x == 'Presença').sum(), lambda x: (x == 'Falta').sum()]
                    }).reset_index()
                    
                    freq_por_aluno.columns = ['id_aluno', 'Total Registros', 'Presenças', 'Faltas']
                    freq_por_aluno['Taxa Presença (%)'] = (
                        freq_por_aluno['Presenças'] / freq_por_aluno['Total Registros'] * 100
                    ).round(1)
                    
                    alunos_com_freq = pd.merge(alunos_na_turma, freq_por_aluno, on='id_aluno', how='left')
                    alunos_com_freq = alunos_com_freq.fillna(0)
                    
                    st.markdown('<div class="data-table">', unsafe_allow_html=True)
                    st.dataframe(
                        alunos_com_freq[['id_aluno', 'nome', 'Total Registros', 'Presenças', 'Faltas', 'Taxa Presença (%)']],
                        use_container_width=True
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="data-table">', unsafe_allow_html=True)
                    st.dataframe(alunos_na_turma[['id_aluno', 'nome']], use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ Nenhum aluno encontrado nesta turma.")
    else:
        st.warning("⚠️ Nenhuma turma cadastrada no sistema.")

with tab2:
    st.subheader("📊 Analytics Avançadas de Frequência")
    
    if not df_frequencia_completa.empty:
        # Filtros de análise
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            periodo_analise = st.selectbox(
                "📅 Período de Análise:",
                ["Último Mês", "Últimos 3 Meses", "Últimos 6 Meses", "Todo o Período"]
            )
        
        with col2:
            turmas_analise = st.multiselect(
                "🏫 Turmas para Análise:",
                df_frequencia_completa['turma'].unique(),
                default=df_frequencia_completa['turma'].unique()
            )
        
        with col3:
            tipo_analise = st.selectbox(
                "📈 Tipo de Análise:",
                ["Frequência Geral", "Análise de Faltas", "Performance por Professor"]
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Filtrar dados por período
        hoje = datetime.now()
        if periodo_analise == "Último Mês":
            data_inicio = hoje - pd.DateOffset(months=1)
        elif periodo_analise == "Últimos 3 Meses":
            data_inicio = hoje - pd.DateOffset(months=3)
        elif periodo_analise == "Últimos 6 Meses":
            data_inicio = hoje - pd.DateOffset(months=6)
        else:
            data_inicio = df_frequencia_completa['data'].min()
        
        df_filtrado = df_frequencia_completa[
            (df_frequencia_completa['data'] >= data_inicio) &
            (df_frequencia_completa['turma'].isin(turmas_analise))
        ]
        
        if not df_filtrado.empty:
            if tipo_analise == "Frequência Geral":
                # Análise de frequência geral
                col1, col2 = st.columns(2)
                
                with col1:
                    # Tendência temporal
                    freq_temporal = df_filtrado.groupby([
                        df_filtrado['data'].dt.to_period('W'), 'status'
                    ]).size().unstack(fill_value=0).reset_index()
                    freq_temporal['data'] = freq_temporal['data'].astype(str)
                    
                    fig_temporal = px.line(
                        freq_temporal.melt(id_vars=['data'], var_name='Status', value_name='Quantidade'),
                        x='data', y='Quantidade', color='Status',
                        title="Tendência Semanal de Frequência",
                        color_discrete_map={'Presença': '#28a745', 'Falta': '#dc3545'}
                    )
                    fig_temporal.update_layout(height=400)
                    st.plotly_chart(fig_temporal, use_container_width=True)
                
                with col2:
                    # Distribuição por turma
                    freq_turma = df_filtrado.groupby(['turma', 'status']).size().unstack(fill_value=0)
                    freq_turma['Total'] = freq_turma.sum(axis=1)
                    freq_turma['Taxa_Presença'] = (freq_turma.get('Presença', 0) / freq_turma['Total'] * 100).round(1)
                    
                    fig_turma = px.bar(
                        freq_turma.reset_index(),
                        x='turma', y='Taxa_Presença',
                        title="Taxa de Presença por Turma (%)",
                        color='Taxa_Presença',
                        color_continuous_scale=['red', 'yellow', 'green']
                    )
                    fig_turma.update_layout(height=400)
                    st.plotly_chart(fig_turma, use_container_width=True)
                
                # Estatísticas resumo
                col1, col2, col3, col4 = st.columns(4)
                
                total_presencas = len(df_filtrado[df_filtrado['status'] == 'Presença'])
                total_faltas = len(df_filtrado[df_filtrado['status'] == 'Falta'])
                taxa_geral = (total_presencas / (total_presencas + total_faltas) * 100) if (total_presencas + total_faltas) > 0 else 0
                
                with col1:
                    st.markdown(f"""
                    <div class="success-card">
                        <h3>✅ {total_presencas}</h3>
                        <p>Total de Presenças</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="warning-card">
                        <h3>❌ {total_faltas}</h3>
                        <p>Total de Faltas</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="stat-card">
                        <h3>📊 {taxa_geral:.1f}%</h3>
                        <p>Taxa Geral de Presença</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    dias_unicos = df_filtrado['data'].dt.date.nunique()
                    st.markdown(f"""
                    <div class="stat-card">
                        <h3>📅 {dias_unicos}</h3>
                        <p>Dias com Registro</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            elif tipo_analise == "Análise de Faltas":
                st.markdown("#### 🔍 Análise Detalhada de Faltas")
                
                # Top alunos com mais faltas
                faltas_por_aluno = df_filtrado[df_filtrado['status'] == 'Falta'].groupby(['id_aluno', 'nome', 'turma']).size().reset_index(name='total_faltas')
                faltas_por_aluno = faltas_por_aluno.sort_values('total_faltas', ascending=False).head(10)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_faltas = px.bar(
                        faltas_por_aluno,
                        x='total_faltas', y='nome',
                        title="Top 10 Alunos com Mais Faltas",
                        orientation='h',
                        color='turma'
                    )
                    fig_faltas.update_layout(height=400)
                    st.plotly_chart(fig_faltas, use_container_width=True)
                
                with col2:
                    # Justificativas de faltas
                    justificativas = df_filtrado[df_filtrado['status'] == 'Falta']['justificativa'].value_counts()
                    
                    fig_just = px.pie(
                        values=justificativas.values,
                        names=justificativas.index,
                        title="Distribuição de Justificativas",
                        hole=0.4
                    )
                    fig_just.update_layout(height=400)
                    st.plotly_chart(fig_just, use_container_width=True)
                
                # Tabela detalhada
                st.markdown("##### 📋 Detalhamento de Alunos com Altas Taxas de Falta")
                st.markdown('<div class="data-table">', unsafe_allow_html=True)
                st.dataframe(faltas_por_aluno, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            st.info("📊 Nenhum dado encontrado para o período e filtros selecionados.")
    else:
        st.info("📊 Nenhum dado de frequência disponível para análise.")

with tab3:
    st.subheader("👨‍🏫 Monitoramento de Atividade dos Professores")
    
    if not df_frequencia_completa.empty:
        # Atividade por professor
        atividade_prof = df_frequencia_completa.groupby('professor').agg({
            'data': ['count', 'min', 'max'],
            'turma': 'nunique'
        }).reset_index()
        
        atividade_prof.columns = ['Professor', 'Total_Registros', 'Primeiro_Registro', 'Ultimo_Registro', 'Turmas_Atendidas']
        atividade_prof['Dias_Ativo'] = (atividade_prof['Ultimo_Registro'] - atividade_prof['Primeiro_Registro']).dt.days + 1
        atividade_prof['Media_Registros_Dia'] = (atividade_prof['Total_Registros'] / atividade_prof['Dias_Ativo']).round(2)
        
        # Gráficos de atividade
        col1, col2 = st.columns(2)
        
        with col1:
            fig_prof = px.bar(
                atividade_prof.sort_values('Total_Registros', ascending=True),
                x='Total_Registros', y='Professor',
                title="Total de Registros por Professor",
                orientation='h',
                color='Total_Registros',
                color_continuous_scale='Viridis'
            )
            fig_prof.update_layout(height=400)
            st.plotly_chart(fig_prof, use_container_width=True)
        
        with col2:
            fig_turmas = px.bar(
                atividade_prof,
                x='Professor', y='Turmas_Atendidas',
                title="Número de Turmas por Professor",
                color='Turmas_Atendidas',
                color_continuous_scale='Blues'
            )
            fig_turmas.update_layout(height=400)
            st.plotly_chart(fig_turmas, use_container_width=True)
        
        # Tabela detalhada
        st.markdown("##### 📊 Detalhamento da Atividade dos Professores")
        st.markdown('<div class="data-table">', unsafe_allow_html=True)
        st.dataframe(
            atividade_prof[['Professor', 'Total_Registros', 'Turmas_Atendidas', 'Media_Registros_Dia', 'Ultimo_Registro']],
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Registros mais recentes
        st.markdown("##### ⏱️ Registros Mais Recentes")
        registros_recentes = df_frequencia_completa[['data', 'nome', 'turma', 'status', 'justificativa', 'professor']].sort_values(by='data', ascending=False).head(15)
        
        st.markdown('<div class="data-table">', unsafe_allow_html=True)
        st.dataframe(registros_recentes, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.info("👨‍🏫 Nenhum registro de atividade de professores encontrado.")

with tab4:
    st.subheader("📈 Relatórios Detalhados e Exportação")
    
    if not df_frequencia_completa.empty:
        # Opções de relatório
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tipo_relatorio = st.selectbox(
                "📄 Tipo de Relatório:",
                ["Frequência Consolidada", "Relatório por Turma", "Relatório por Professor", "Análise Temporal"]
            )
        
        with col2:
            formato_export = st.selectbox(
                "💾 Formato de Exportação:",
                ["CSV", "Excel", "JSON"]
            )
        
        with col3:
            periodo_relatorio = st.selectbox(
                "📅 Período:",
                ["Último Mês", "Últimos 3 Meses", "Todo o Período"]
            )
        
        # Gerar relatório baseado na seleção
        if tipo_relatorio == "Frequência Consolidada":
            relatorio = df_frequencia_completa.groupby(['turma', 'nome']).agg({
                'status': ['count', lambda x: (x == 'Presença').sum(), lambda x: (x == 'Falta').sum()]
            }).reset_index()
            relatorio.columns = ['Turma', 'Aluno', 'Total_Dias', 'Presencas', 'Faltas']
            relatorio['Taxa_Presenca_%'] = (relatorio['Presencas'] / relatorio['Total_Dias'] * 100).round(2)
            
        elif tipo_relatorio == "Relatório por Turma":
            relatorio = df_frequencia_completa.groupby('turma').agg({
                'id_aluno': 'nunique',
                'status': ['count', lambda x: (x == 'Presença').sum(), lambda x: (x == 'Falta').sum()]
            }).reset_index()
            relatorio.columns = ['Turma', 'Total_Alunos', 'Total_Registros', 'Presencas', 'Faltas']
            relatorio['Taxa_Presenca_%'] = (relatorio['Presencas'] / relatorio['Total_Registros'] * 100).round(2)
            
        elif tipo_relatorio == "Relatório por Professor":
            relatorio = df_frequencia_completa.groupby('professor').agg({
                'turma': 'nunique',
                'id_aluno': 'nunique',
                'status': 'count',
                'data': ['min', 'max']
            }).reset_index()
            relatorio.columns = ['Professor', 'Turmas_Atendidas', 'Alunos_Registrados', 'Total_Registros', 'Primeiro_Registro', 'Ultimo_Registro']
            
        else:  # Análise Temporal
            relatorio = df_frequencia_completa.groupby(df_frequencia_completa['data'].dt.to_period('M')).agg({
                'status': ['count', lambda x: (x == 'Presença').sum(), lambda x: (x == 'Falta').sum()],
                'turma': 'nunique',
                'id_aluno': 'nunique'
            }).reset_index()
            relatorio.columns = ['Mes', 'Total_Registros', 'Presencas', 'Faltas', 'Turmas_Ativas', 'Alunos_Registrados']
            relatorio['Mes'] = relatorio['Mes'].astype(str)
        
        # Exibir relatório
        st.markdown("##### 📊 Visualização do Relatório")
        st.markdown('<div class="data-table">', unsafe_allow_html=True)
        st.dataframe(relatorio, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botão de download
        if formato_export == "CSV":
            csv = relatorio.to_csv(index=False)
            st.download_button(
                label=f"⬇️ Baixar Relatório ({tipo_relatorio}) - CSV",
                data=csv,
                file_name=f"relatorio_{tipo_relatorio.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        elif formato_export == "JSON":
            json_str = relatorio.to_json(orient='records', indent=2)
            st.download_button(
                label=f"⬇️ Baixar Relatório ({tipo_relatorio}) - JSON",
                data=json_str,
                file_name=f"relatorio_{tipo_relatorio.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    else:
        st.info("📈 Nenhum dado disponível para gerar relatórios.")

with tab5:
    st.subheader("⚙️ Administração do Sistema")
    
    # Seção de informações do sistema
    st.markdown("#### 📊 Informações do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.write("**📈 Estatísticas Gerais:**")
        st.write(f"• Total de registros no sistema: {len(df_frequencia)}")
        st.write(f"• Período de dados: {df_frequencia_completa['data'].min().strftime('%d/%m/%Y') if not df_frequencia_completa.empty else 'N/A'} até {df_frequencia_completa['data'].max().strftime('%d/%m/%Y') if not df_frequencia_completa.empty else 'N/A'}")
        st.write(f"• Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.write("**🔧 Operações Disponíveis:**")
        st.write("• Limpeza de dados")
        st.write("• Reset do sistema")
        st.write("• Backup/Restauração")
        st.write("• Manutenção de arquivos")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Zona de perigo - Reset do sistema
    st.markdown("#### ⚠️ Zona de Administração Crítica")
    
    st.markdown('<div class="danger-zone">', unsafe_allow_html=True)
    st.warning("🚨 **ATENÇÃO:** As operações abaixo são irreversíveis e afetarão todo o sistema!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🗑️ Limpeza de Dados")
        
        # Opções de limpeza
        limpar_frequencia = st.checkbox("🗂️ Limpar todos os registros de frequência")
        limpar_turmas = st.checkbox("🏫 Limpar dados de turmas")
        limpar_alunos = st.checkbox("👥 Limpar dados de alunos")
        
        if st.button("🗑️ Executar Limpeza Selecionada", type="secondary"):
            if limpar_frequencia or limpar_turmas or limpar_alunos:
                # Confirmação adicional
                confirmacao = st.text_input("Digite 'CONFIRMAR' para executar a limpeza:", key="confirm_clean")
                
                if confirmacao == "CONFIRMAR":
                    try:
                        if limpar_frequencia:
                            # Criar DataFrame vazio e salvar
                            df_vazio_freq = pd.DataFrame(columns=['id_aluno', 'data', 'status', 'justificativa', 'professor'])
                            save_data(df_vazio_freq, FREQUENCIA_FILE)
                            st.success("✅ Registros de frequência limpos!")
                        
                        if limpar_turmas:
                            df_vazio_turmas = pd.DataFrame(columns=['nome_turma'])
                            save_data(df_vazio_turmas, TURMAS_FILE)
                            st.success("✅ Dados de turmas limpos!")
                        
                        if limpar_alunos:
                            df_vazio_alunos = pd.DataFrame(columns=['id_aluno', 'nome', 'turma'])
                            save_data(df_vazio_alunos, ALUNOS_FILE)
                            st.success("✅ Dados de alunos limpos!")
                        
                        # Limpar cache
                        st.cache_data.clear()
                        st.balloons()
                        
                        # Recarregar página após 2 segundos
                        import time
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro durante a limpeza: {str(e)}")
                elif confirmacao and confirmacao != "CONFIRMAR":
                    st.error("❌ Confirmação incorreta. Digite exatamente 'CONFIRMAR'")
            else:
                st.warning("⚠️ Selecione pelo menos uma opção para limpeza.")
    
    with col2:
        st.markdown("##### 🔄 Reset Completo do Sistema")
        
        st.write("**Esta operação irá:**")
        st.write("• ❌ Apagar TODOS os registros de frequência")
        st.write("• ❌ Apagar TODAS as turmas cadastradas")
        st.write("• ❌ Apagar TODOS os alunos matriculados")
        st.write("• 🔄 Resetar o sistema para estado inicial")
        
        reset_confirmacao = st.text_input(
            "Para resetar TUDO, digite 'RESET COMPLETO':",
            key="reset_confirmation"
        )
        
        if st.button("🔄 RESET COMPLETO DO SISTEMA", type="primary"):
            if reset_confirmacao == "RESET COMPLETO":
                try:
                    # Criar DataFrames vazios
                    df_freq_vazio = pd.DataFrame(columns=['id_aluno', 'data', 'status', 'justificativa', 'professor'])
                    df_turmas_vazio = pd.DataFrame(columns=['nome_turma'])
                    df_alunos_vazio = pd.DataFrame(columns=['id_aluno', 'nome', 'turma'])
                    
                    # Salvar arquivos vazios
                    save_data(df_freq_vazio, FREQUENCIA_FILE)
                    save_data(df_turmas_vazio, TURMAS_FILE)
                    save_data(df_alunos_vazio, ALUNOS_FILE)
                    
                    # Limpar todo o cache
                    st.cache_data.clear()
                    
                    st.success("🎉 Sistema resetado com sucesso!")
                    st.info("🔄 Recarregando o dashboard...")
                    
                    # Aguardar e recarregar
                    import time
                    time.sleep(3)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro durante o reset: {str(e)}")
                    
            elif reset_confirmacao and reset_confirmacao != "RESET COMPLETO":
                st.error("❌ Confirmação incorreta. Digite exatamente 'RESET COMPLETO'")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Seção de backup e manutenção
    st.markdown("#### 💾 Backup e Manutenção")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📦 Backup dos Dados")
        
        if st.button("💾 Gerar Backup Completo"):
            try:
                # Criar backup em formato JSON
                backup_data = {
                    "timestamp": datetime.now().isoformat(),
                    "frequencia": df_frequencia.to_dict('records') if not df_frequencia.empty else [],
                    "turmas": df_turmas.to_dict('records') if not df_turmas.empty else [],
                    "alunos": df_alunos.to_dict('records') if not df_alunos.empty else []
                }
                
                import json
                backup_json = json.dumps(backup_data, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="⬇️ Baixar Backup Completo",
                    data=backup_json,
                    file_name=f"backup_sistema_frequencia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
                st.success("✅ Backup gerado com sucesso!")
                
            except Exception as e:
                st.error(f"❌ Erro ao gerar backup: {str(e)}")
    
    with col2:
        st.markdown("##### 🔧 Ferramentas de Manutenção")
        
        # Verificar integridade dos dados
        if st.button("🔍 Verificar Integridade dos Dados"):
            problemas = []
            
            # Verificar se há alunos órfãos na frequência
            if not df_frequencia.empty and not df_alunos.empty:
                alunos_freq = set(df_frequencia['id_aluno'].unique())
                alunos_cadastrados = set(df_alunos['id_aluno'].unique())
                alunos_orfaos = alunos_freq - alunos_cadastrados
                
                if alunos_orfaos:
                    problemas.append(f"🔸 {len(alunos_orfaos)} registros de frequência com alunos não cadastrados")
            
            # Verificar turmas órfãs
            if not df_alunos.empty and not df_turmas.empty:
                turmas_alunos = set(df_alunos['turma'].unique())
                turmas_cadastradas = set(df_turmas['nome_turma'].unique())
                turmas_orfas = turmas_alunos - turmas_cadastradas
                
                if turmas_orfas:
                    problemas.append(f"🔸 {len(turmas_orfas)} alunos em turmas não cadastradas")
            
            # Verificar duplicatas
            if not df_alunos.empty:
                duplicatas_alunos = df_alunos[df_alunos.duplicated(['id_aluno'])]
                if not duplicatas_alunos.empty:
                    problemas.append(f"🔸 {len(duplicatas_alunos)} alunos com IDs duplicados")
            
            if not df_frequencia.empty:
                duplicatas_freq = df_frequencia[df_frequencia.duplicated(['id_aluno', 'data'])]
                if not duplicatas_freq.empty:
                    problemas.append(f"🔸 {len(duplicatas_freq)} registros de frequência duplicados")
            
            # Exibir resultados
            if problemas:
                st.warning("⚠️ **Problemas encontrados:**")
                for problema in problemas:
                    st.write(problema)
            else:
                st.success("✅ **Integridade dos dados verificada:** Nenhum problema encontrado!")
        
        # Limpar cache manualmente
        if st.button("🧹 Limpar Cache do Sistema"):
            st.cache_data.clear()
            st.success("✅ Cache limpo com sucesso!")
            st.info("🔄 Recomenda-se recarregar a página.")
    
    # Informações de debug (apenas para desenvolvimento)
    with st.expander("🔧 Informações Técnicas (Debug)"):
        st.write("**Arquivos de dados:**")
        st.code(f"""
        FREQUENCIA_FILE: {FREQUENCIA_FILE}
        TURMAS_FILE: {TURMAS_FILE}
        ALUNOS_FILE: {ALUNOS_FILE}
        """)
        
        st.write("**Estado atual dos DataFrames:**")
        st.write(f"• df_frequencia: {len(df_frequencia)} registros")
        st.write(f"• df_turmas: {len(df_turmas)} registros")  
        st.write(f"• df_alunos: {len(df_alunos)} registros")
        st.write(f"• df_frequencia_completa: {len(df_frequencia_completa)} registros")
        
        if st.checkbox("Mostrar estrutura dos dados"):
            if not df_frequencia.empty:
                st.write("**Estrutura df_frequencia:**")
                st.write(df_frequencia.dtypes)
            if not df_alunos.empty:
                st.write("**Estrutura df_alunos:**")
                st.write(df_alunos.dtypes)
            if not df_turmas.empty:
                st.write("**Estrutura df_turmas:**")
                st.write(df_turmas.dtypes)

# Footer com informações do sistema
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>📊 Dashboard Administrativo - Sistema de Controle de Frequência</p>
    <p>🕐 Última atualização: {}</p>
</div>
""".format(datetime.now().strftime('%d/%m/%Y %H:%M:%S')), unsafe_allow_html=True)