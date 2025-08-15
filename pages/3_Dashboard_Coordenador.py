import streamlit as st
import pandas as pd
import numpy as np
from utils.database import get_data, FREQUENCIA_FILE, TURMAS_FILE, ALUNOS_FILE
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF
from io import BytesIO
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="Dashboard Coordenador",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para melhor visual
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4 0%, #17becf 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .alert-high { background-color: #ffebee; border-left: 4px solid #f44336; padding: 1rem; }
    .alert-medium { background-color: #fff3e0; border-left: 4px solid #ff9800; padding: 1rem; }
    .alert-low { background-color: #e8f5e8; border-left: 4px solid #4caf50; padding: 1rem; }
    .insight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 16px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Verificação de permissão
if st.session_state.get("role") != "coordenador":
    st.error("🚫 Você não tem permissão para acessar esta página.")
    st.stop()

# Header principal
st.markdown("""
<div class="main-header">
    <h1>📊 Dashboard do Coordenador</h1>
    <p>Sistema Avançado de Monitoramento Acadêmico</p>
</div>
""", unsafe_allow_html=True)

# Carregamento de dados com cache
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_all_data():
    """Carrega e processa todos os dados necessários"""
    df_frequencia = get_data(FREQUENCIA_FILE)
    df_turmas = get_data(TURMAS_FILE)
    df_alunos = get_data(ALUNOS_FILE)
    
    if not df_frequencia.empty:
        df_frequencia['data'] = pd.to_datetime(df_frequencia['data'])
        df_frequencia = pd.merge(
            df_frequencia, 
            df_alunos[['id_aluno', 'nome', 'turma']], 
            on='id_aluno', 
            how='left'
        )
        df_frequencia['mes'] = df_frequencia['data'].dt.strftime('%Y-%m')
        df_frequencia['semana'] = df_frequencia['data'].dt.isocalendar().week
        df_frequencia['dia_semana'] = df_frequencia['data'].dt.day_name()
    
    return df_frequencia, df_turmas, df_alunos

# Carrega dados
with st.spinner("📊 Carregando dados..."):
    df_frequencia, df_turmas, df_alunos = load_all_data()

# Sidebar com filtros avançados
with st.sidebar:
    st.markdown("### 🎛️ Filtros Avançados")
    
    # Filtro de data
    if not df_frequencia.empty:
        data_min = df_frequencia['data'].min().date()
        data_max = df_frequencia['data'].max().date()
        
        periodo_selecionado = st.date_input(
            "📅 Período de Análise",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max
        )
        
        if len(periodo_selecionado) == 2:
            inicio, fim = periodo_selecionado
            df_filtrado = df_frequencia[
                (df_frequencia['data'].dt.date >= inicio) & 
                (df_frequencia['data'].dt.date <= fim)
            ]
        else:
            df_filtrado = df_frequencia
        
        # Filtro por turma
        turmas_disponiveis = ['Todas'] + sorted(df_filtrado['turma'].dropna().unique().tolist())
        turma_selecionada = st.selectbox("🎓 Turma", turmas_disponiveis)
        
        if turma_selecionada != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['turma'] == turma_selecionada]
        
        # Métricas rápidas na sidebar
        st.markdown("### 📈 Métricas Rápidas")
        total_registros = len(df_filtrado)
        total_faltas = len(df_filtrado[df_filtrado['status'] == 'Falta'])
        taxa_presenca = ((total_registros - total_faltas) / total_registros * 100) if total_registros > 0 else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Registros", f"{total_registros:,}")
        with col2:
            st.metric("Taxa Presença", f"{taxa_presenca:.1f}%")
    else:
        st.warning("Nenhum dado disponível")
        df_filtrado = df_frequencia

# Verificação de dados
if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado encontrado para o período selecionado.")
    st.stop()

# Tabs principais
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Visão Geral", 
    "📈 Analytics Avançada", 
    "🎯 Insights IA", 
    "📋 Relatórios", 
    "🚨 Alertas"
])

with tab1:
    st.header("📊 Visão Geral do Sistema")
    
    # KPIs principais
    col1, col2, col3, col4 = st.columns(4)
    
    total_alunos = df_alunos['id_aluno'].nunique() if not df_alunos.empty else 0
    # Verificar colunas disponíveis em df_turmas e usar a primeira coluna disponível
    if not df_turmas.empty:
        # Tentar diferentes possíveis nomes de colunas
        if 'nome' in df_turmas.columns:
            total_turmas = df_turmas['nome'].nunique()
        elif 'turma' in df_turmas.columns:
            total_turmas = df_turmas['turma'].nunique()
        elif 'id_turma' in df_turmas.columns:
            total_turmas = df_turmas['id_turma'].nunique()
        else:
            # Se não encontrar nenhuma coluna conhecida, usar a primeira coluna
            total_turmas = df_turmas.iloc[:, 0].nunique()
    else:
        total_turmas = 0
    
    taxa_falta = (len(df_filtrado[df_filtrado['status'] == 'Falta']) / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
    
    # Simplificar cálculo de alunos críticos
    if len(df_filtrado) > 0:
        alunos_faltas = df_filtrado.groupby('id_aluno')['status'].apply(
            lambda x: (x == 'Falta').sum() / x.count()
        )
        alunos_criticos = len(alunos_faltas[alunos_faltas > 0.3])
    else:
        alunos_criticos = 0
    
    with col1:
        st.metric("👥 Total de Alunos", f"{total_alunos:,}")
    with col2:
        st.metric("🎓 Total de Turmas", f"{total_turmas:,}")
    with col3:
        delta_color = "inverse" if taxa_falta > 10 else "normal"
        st.metric("📉 Taxa de Faltas", f"{taxa_falta:.1f}%", delta=f"{taxa_falta-15:.1f}%")
    with col4:
        st.metric("🚨 Alunos Críticos", f"{alunos_criticos:,}", delta=f"{alunos_criticos-5:,}")
    
    st.markdown("---")
    
    # Gráficos principais
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribuição de frequência
        status_counts = df_filtrado['status'].value_counts()
        fig_pie = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="📊 Distribuição Geral de Frequência",
            color_discrete_map={'Presença': '#00b33c', 'Falta': '#ff3300'},
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=400, showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Frequência por turma
        freq_turma = df_filtrado.groupby(['turma', 'status']).size().reset_index(name='count')
        fig_bar = px.bar(
            freq_turma,
            x='turma',
            y='count',
            color='status',
            title="📈 Frequência por Turma",
            color_discrete_map={'Presença': '#00b33c', 'Falta': '#ff3300'},
            barmode='group'
        )
        fig_bar.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Timeline de frequência
    st.subheader("📅 Timeline de Frequência")
    freq_timeline = df_filtrado.groupby(['data', 'status']).size().reset_index(name='count')
    fig_timeline = px.line(
        freq_timeline,
        x='data',
        y='count',
        color='status',
        title="Evolução Temporal da Frequência",
        color_discrete_map={'Presença': '#00b33c', 'Falta': '#ff3300'}
    )
    fig_timeline.update_layout(height=400)
    st.plotly_chart(fig_timeline, use_container_width=True)

with tab2:
    st.header("📈 Analytics Avançada")
    
    # Heatmap de faltas por dia da semana e turma
    st.subheader("🔥 Mapa de Calor: Faltas por Dia da Semana")
    
    faltas_heatmap = df_filtrado[df_filtrado['status'] == 'Falta'].groupby(['dia_semana', 'turma']).size().reset_index(name='faltas')
    faltas_pivot = faltas_heatmap.pivot(index='dia_semana', columns='turma', values='faltas').fillna(0)
    
    if not faltas_pivot.empty:
        fig_heatmap = px.imshow(
            faltas_pivot.values,
            x=faltas_pivot.columns,
            y=faltas_pivot.index,
            color_continuous_scale='Reds',
            title="Intensidade de Faltas por Dia da Semana e Turma",
            labels={'color': 'Número de Faltas'}
        )
        fig_heatmap.update_layout(height=400)
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top 10 alunos com mais faltas
        st.subheader("🎯 Ranking de Faltas por Aluno")
        
        aluno_faltas = df_filtrado[df_filtrado['status'] == 'Falta'].groupby(['nome', 'turma']).size().reset_index(name='total_faltas')
        aluno_total = df_filtrado.groupby(['nome', 'turma']).size().reset_index(name='total_registros')
        ranking_faltas = pd.merge(aluno_faltas, aluno_total, on=['nome', 'turma'], how='right').fillna(0)
        ranking_faltas['percentual_faltas'] = ranking_faltas['total_faltas'] / ranking_faltas['total_registros'] * 100
        ranking_faltas = ranking_faltas.sort_values('percentual_faltas', ascending=False).head(10)
        
        if not ranking_faltas.empty:
            fig_ranking = px.bar(
                ranking_faltas,
                x='percentual_faltas',
                y='nome',
                orientation='h',
                title="Top 10 Alunos com Maior % de Faltas",
                color='percentual_faltas',
                color_continuous_scale='Reds'
            )
            fig_ranking.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_ranking, use_container_width=True)
    
    with col2:
        # Análise por turma
        st.subheader("📚 Performance por Turma")
        
        turma_stats = df_filtrado.groupby('turma').agg({
            'status': ['count', lambda x: (x == 'Falta').sum()]
        }).round(2)
        turma_stats.columns = ['Total_Registros', 'Total_Faltas']
        turma_stats['Taxa_Presenca'] = ((turma_stats['Total_Registros'] - turma_stats['Total_Faltas']) / turma_stats['Total_Registros'] * 100).round(1)
        turma_stats = turma_stats.reset_index().sort_values('Taxa_Presenca')
        
        fig_turma_perf = px.bar(
            turma_stats,
            x='turma',
            y='Taxa_Presenca',
            title="Taxa de Presença por Turma (%)",
            color='Taxa_Presenca',
            color_continuous_scale='RdYlGn'
        )
        fig_turma_perf.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig_turma_perf, use_container_width=True)
    
    # Análise temporal avançada
    st.subheader("⏰ Análise Temporal Avançada")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Faltas por mês
        faltas_mes = df_filtrado[df_filtrado['status'] == 'Falta'].groupby('mes').size().reset_index(name='faltas')
        fig_mes = px.line(
            faltas_mes,
            x='mes',
            y='faltas',
            title="Evolução de Faltas por Mês",
            markers=True
        )
        fig_mes.update_layout(height=300, xaxis_tickangle=-45)
        st.plotly_chart(fig_mes, use_container_width=True)
    
    with col2:
        # Faltas por dia da semana
        faltas_dia = df_filtrado[df_filtrado['status'] == 'Falta'].groupby('dia_semana').size().reset_index(name='faltas')
        dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        faltas_dia['dia_semana'] = pd.Categorical(faltas_dia['dia_semana'], categories=dias_ordem, ordered=True)
        faltas_dia = faltas_dia.sort_values('dia_semana')
        
        fig_dia = px.bar(
            faltas_dia,
            x='dia_semana',
            y='faltas',
            title="Faltas por Dia da Semana",
            color='faltas',
            color_continuous_scale='Oranges'
        )
        fig_dia.update_layout(height=300, xaxis_tickangle=-45)
        st.plotly_chart(fig_dia, use_container_width=True)
    
    with col3:
        # Distribuição de justificativas
        if 'justificativa' in df_filtrado.columns:
            just_counts = df_filtrado[df_filtrado['status'] == 'Falta']['justificativa'].value_counts().head(5)
            fig_just = px.pie(
                values=just_counts.values,
                names=just_counts.index,
                title="Top 5 Justificativas"
            )
            fig_just.update_layout(height=300)
            st.plotly_chart(fig_just, use_container_width=True)

with tab3:
    st.header("🎯 Insights com Inteligência Artificial")
    
    # Função para gerar insights automáticos
    def gerar_insights(df):
        insights = []
        
        # Insight 1: Taxa geral de faltas
        taxa_falta_geral = len(df[df['status'] == 'Falta']) / len(df) * 100 if len(df) > 0 else 0
        if taxa_falta_geral > 15:
            insights.append({
                'tipo': 'critico',
                'titulo': '🚨 Taxa de Faltas Crítica',
                'descricao': f'A taxa geral de faltas está em {taxa_falta_geral:.1f}%, acima do limite recomendado de 15%.',
                'acao': 'Implementar programa de acompanhamento personalizado para alunos com alta taxa de faltas.'
            })
        
        # Insight 2: Padrões temporais
        if not df.empty:
            faltas_por_dia = df[df['status'] == 'Falta'].groupby('dia_semana').size()
            if len(faltas_por_dia) > 0:
                dia_maior_falta = faltas_por_dia.idxmax()
                insights.append({
                    'tipo': 'medio',
                    'titulo': '📅 Padrão Temporal Identificado',
                    'descricao': f'O maior número de faltas ocorre às {dia_maior_falta}s.',
                    'acao': f'Revisar atividades e metodologias aplicadas às {dia_maior_falta}s.'
                })
        
        # Insight 3: Turmas em risco
        if not df.empty:
            turma_stats = df.groupby('turma')['status'].apply(
                lambda x: (x == 'Falta').sum() / x.count() * 100
            ).sort_values(ascending=False)
            
            if len(turma_stats) > 0 and turma_stats.iloc[0] > 20:
                insights.append({
                    'tipo': 'critico',
                    'titulo': '🎓 Turma em Situação Crítica',
                    'descricao': f'A turma {turma_stats.index[0]} apresenta {turma_stats.iloc[0]:.1f}% de faltas.',
                    'acao': 'Reunião urgente com professores e coordenação para análise da situação.'
                })
        
        # Insight 4: Alunos que necessitam atenção especial
        if not df.empty:
            alunos_criticos = df.groupby(['nome', 'turma'])['status'].apply(
                lambda x: (x == 'Falta').sum() / x.count() > 0.3
            ).sum()
            
            if alunos_criticos > 0:
                insights.append({
                    'tipo': 'medio',
                    'titulo': '👤 Alunos Necessitam Atenção',
                    'descricao': f'{alunos_criticos} aluno(s) apresentam mais de 30% de faltas.',
                    'acao': 'Agendar reunião individual com alunos e responsáveis.'
                })
        
        # Insight 5: Tendência temporal
        if not df.empty and 'data' in df.columns:
            df_recente = df[df['data'] >= df['data'].max() - timedelta(days=30)]
            df_anterior = df[(df['data'] >= df['data'].max() - timedelta(days=60)) & 
                           (df['data'] < df['data'].max() - timedelta(days=30))]
            
            if len(df_recente) > 0 and len(df_anterior) > 0:
                taxa_recente = len(df_recente[df_recente['status'] == 'Falta']) / len(df_recente) * 100
                taxa_anterior = len(df_anterior[df_anterior['status'] == 'Falta']) / len(df_anterior) * 100
                variacao = taxa_recente - taxa_anterior
                
                if abs(variacao) > 5:
                    tipo_trend = 'critico' if variacao > 0 else 'positivo'
                    emoji = '📈' if variacao > 0 else '📉'
                    insights.append({
                        'tipo': tipo_trend,
                        'titulo': f'{emoji} Tendência nos Últimos 30 Dias',
                        'descricao': f'A taxa de faltas {"aumentou" if variacao > 0 else "diminuiu"} {abs(variacao):.1f}% em relação ao mês anterior.',
                        'acao': 'Analisar fatores que influenciaram esta mudança na tendência.'
                    })
        
        return insights
    
    # Gerar e exibir insights
    insights = gerar_insights(df_filtrado)
    
    if insights:
        for insight in insights:
            if insight['tipo'] == 'critico':
                st.markdown(f"""
                <div class="alert-high">
                    <h4>{insight['titulo']}</h4>
                    <p><strong>Situação:</strong> {insight['descricao']}</p>
                    <p><strong>Recomendação:</strong> {insight['acao']}</p>
                </div>
                """, unsafe_allow_html=True)
            elif insight['tipo'] == 'medio':
                st.markdown(f"""
                <div class="alert-medium">
                    <h4>{insight['titulo']}</h4>
                    <p><strong>Situação:</strong> {insight['descricao']}</p>
                    <p><strong>Recomendação:</strong> {insight['acao']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="alert-low">
                    <h4>{insight['titulo']}</h4>
                    <p><strong>Situação:</strong> {insight['descricao']}</p>
                    <p><strong>Recomendação:</strong> {insight['acao']}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("🎯 Nenhum insight crítico identificado no momento. O sistema está operando dentro dos parâmetros normais.")
    
    # Previsões e recomendações
    st.subheader("🔮 Análise Preditiva")
    
    if not df_filtrado.empty:
        # Simulação de predição de risco
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="insight-box">
                <h4>🎯 Modelo de Risco de Evasão</h4>
                <p>Com base nos padrões de frequência:</p>
                <ul>
                    <li>Alunos com >40% de faltas: <strong>Alto Risco</strong></li>
                    <li>Alunos com 20-40% de faltas: <strong>Médio Risco</strong></li>
                    <li>Alunos com <20% de faltas: <strong>Baixo Risco</strong></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Calcular distribuição de risco
            if not df_filtrado.empty:
                risco_dist = df_filtrado.groupby('nome')['status'].apply(
                    lambda x: (x == 'Falta').sum() / x.count() * 100
                ).reset_index(name='perc_faltas')
                
                risco_dist['categoria'] = pd.cut(
                    risco_dist['perc_faltas'],
                    bins=[0, 20, 40, 100],
                    labels=['Baixo Risco', 'Médio Risco', 'Alto Risco']
                )
                
                risco_counts = risco_dist['categoria'].value_counts()
                
                fig_risco = px.pie(
                    values=risco_counts.values,
                    names=risco_counts.index,
                    title="Distribuição de Risco de Evasão",
                    color_discrete_map={
                        'Baixo Risco': '#4caf50',
                        'Médio Risco': '#ff9800', 
                        'Alto Risco': '#f44336'
                    }
                )
                st.plotly_chart(fig_risco, use_container_width=True)

with tab4:
    st.header("📋 Relatórios Avançados")
    
    # Seletor de tipo de relatório
    tipo_relatorio = st.selectbox(
        "Selecione o tipo de relatório:",
        ["Relatório Geral", "Relatório por Turma", "Relatório de Alunos Críticos", "Relatório Temporal"]
    )
    
    # Configurações do relatório
    col1, col2, col3 = st.columns(3)
    
    with col1:
        formato_export = st.selectbox("Formato:", ["PDF", "Excel", "CSV"])
    with col2:
        incluir_graficos = st.checkbox("Incluir Gráficos", value=True)
    with col3:
        periodo_relatorio = st.selectbox("Período:", ["Último Mês", "Últimos 3 Meses", "Todo Período"])
    
    # Preview do relatório
    st.subheader("📄 Preview do Relatório")
    
    if tipo_relatorio == "Relatório Geral":
        # Dados gerais
        col1, col2, col3, col4 = st.columns(4)
        
        total_alunos_rel = df_alunos['id_aluno'].nunique() if not df_alunos.empty else 0
        total_registros_rel = len(df_filtrado)
        taxa_presenca_rel = ((total_registros_rel - len(df_filtrado[df_filtrado['status'] == 'Falta'])) / total_registros_rel * 100) if total_registros_rel > 0 else 0
        media_faltas_aluno = len(df_filtrado[df_filtrado['status'] == 'Falta']) / max(1, total_alunos_rel)
        
        with col1:
            st.metric("Total de Alunos", total_alunos_rel)
        with col2:
            st.metric("Total de Registros", total_registros_rel)
        with col3:
            st.metric("Taxa de Presença", f"{taxa_presenca_rel:.1f}%")
        with col4:
            st.metric("Média Faltas/Aluno", f"{media_faltas_aluno:.1f}")
        
        # Tabela resumo
        if not df_filtrado.empty and 'turma' in df_filtrado.columns:
            resumo_turmas = df_filtrado.groupby('turma').agg({
                'id_aluno': 'nunique',
                'status': ['count', lambda x: (x == 'Falta').sum()]
            }).round(2)
            resumo_turmas.columns = ['Qtd_Alunos', 'Total_Registros', 'Total_Faltas']
            resumo_turmas['Taxa_Presenca'] = ((resumo_turmas['Total_Registros'] - resumo_turmas['Total_Faltas']) / resumo_turmas['Total_Registros'] * 100).round(1)
            
            st.dataframe(resumo_turmas, use_container_width=True)
        else:
            st.warning("Dados insuficientes para gerar resumo por turma")
    
    elif tipo_relatorio == "Relatório de Alunos Críticos":
        # Identificar alunos críticos (>30% de faltas)
        if not df_filtrado.empty and 'nome' in df_filtrado.columns and 'turma' in df_filtrado.columns:
            alunos_criticos_rel = df_filtrado.groupby(['nome', 'turma']).agg({
                'status': ['count', lambda x: (x == 'Falta').sum()]
            }).round(2)
            alunos_criticos_rel.columns = ['Total_Registros', 'Total_Faltas']
            alunos_criticos_rel['Percentual_Faltas'] = (alunos_criticos_rel['Total_Faltas'] / alunos_criticos_rel['Total_Registros'] * 100).round(1)
            alunos_criticos_rel = alunos_criticos_rel[alunos_criticos_rel['Percentual_Faltas'] > 30].reset_index()
            
            if not alunos_criticos_rel.empty:
                st.dataframe(alunos_criticos_rel, use_container_width=True)
                
                st.warning(f"⚠️ Foram identificados {len(alunos_criticos_rel)} alunos em situação crítica (>30% de faltas)")
            else:
                st.success("✅ Nenhum aluno em situação crítica identificado!")
        else:
            st.warning("Dados insuficientes para análise de alunos críticos")
    
    # Função para gerar PDF melhorado
    def gerar_relatorio_pdf(tipo, dados, periodo):
        """Gera relatório PDF com formatação avançada"""
        pdf = FPDF()
        pdf.add_page()
        
        # Cabeçalho
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 15, f"Sistema de Frequência Acadêmica", 0, 1, 'C')
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"{tipo}", 0, 1, 'C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 10, f"Período: {periodo} | Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'C')
        pdf.ln(10)
        
        # Resumo executivo
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "RESUMO EXECUTIVO", 0, 1)
        pdf.set_font("Arial", '', 10)
        
        if not dados.empty:
            total_alunos = dados['nome'].nunique() if 'nome' in dados.columns else 0
            total_registros = len(dados)
            total_faltas = len(dados[dados['status'] == 'Falta']) if 'status' in dados.columns else 0
            taxa_presenca = ((total_registros - total_faltas) / total_registros * 100) if total_registros > 0 else 0
            
            pdf.cell(0, 6, f"• Total de Alunos: {total_alunos}", 0, 1)
            pdf.cell(0, 6, f"• Total de Registros: {total_registros}", 0, 1)
            pdf.cell(0, 6, f"• Taxa de Presença: {taxa_presenca:.1f}%", 0, 1)
            pdf.cell(0, 6, f"• Total de Faltas: {total_faltas}", 0, 1)
        
        pdf.ln(5)
        
        # Detalhamento por turma
        if 'turma' in dados.columns and 'nome' in dados.columns:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, "DETALHAMENTO POR TURMA", 0, 1)
            
            # Cabeçalho da tabela
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(40, 8, "Turma", 1, 0, 'C')
            pdf.cell(30, 8, "Alunos", 1, 0, 'C')
            pdf.cell(35, 8, "Registros", 1, 0, 'C')
            pdf.cell(30, 8, "Faltas", 1, 0, 'C')
            pdf.cell(35, 8, "Taxa Pres.", 1, 1, 'C')
            
            # Dados da tabela
            pdf.set_font("Arial", '', 8)
            turma_stats = dados.groupby('turma').agg({
                'nome': 'nunique',
                'status': ['count', lambda x: (x == 'Falta').sum()]
            }).round(2)
            turma_stats.columns = ['Qtd_Alunos', 'Total_Registros', 'Total_Faltas']
            turma_stats['Taxa_Presenca'] = ((turma_stats['Total_Registros'] - turma_stats['Total_Faltas']) / turma_stats['Total_Registros'] * 100).round(1)
            
            for turma, row in turma_stats.iterrows():
                pdf.cell(40, 6, str(turma)[:15], 1, 0, 'L')  # Limitar tamanho do texto
                pdf.cell(30, 6, str(int(row['Qtd_Alunos'])), 1, 0, 'C')
                pdf.cell(35, 6, str(int(row['Total_Registros'])), 1, 0, 'C')
                pdf.cell(30, 6, str(int(row['Total_Faltas'])), 1, 0, 'C')
                pdf.cell(35, 6, f"{row['Taxa_Presenca']:.1f}%", 1, 1, 'C')
        
        return pdf
    
    # Botão para gerar relatório
    if st.button("📥 Gerar Relatório", type="primary"):
        if not df_filtrado.empty:
            with st.spinner("Gerando relatório..."):
                if formato_export == "PDF":
                    pdf_relatorio = gerar_relatorio_pdf(tipo_relatorio, df_filtrado, f"{periodo_selecionado[0]} a {periodo_selecionado[1]}" if len(periodo_selecionado) == 2 else "Todo período")
                    pdf_output = BytesIO()
                    pdf_string = pdf_relatorio.output(dest='S').encode('latin-1')
                    pdf_output.write(pdf_string)
                    pdf_output.seek(0)
                    
                    st.download_button(
                        label="📄 Baixar Relatório PDF",
                        data=pdf_output,
                        file_name=f"relatorio_{tipo_relatorio.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf"
                    )
                
                elif formato_export == "Excel":
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        # Aba principal com dados
                        df_filtrado.to_excel(writer, sheet_name='Dados_Frequencia', index=False)
                        
                        # Aba com resumo por turma
                        if 'turma' in df_filtrado.columns and 'nome' in df_filtrado.columns:
                            resumo_turmas = df_filtrado.groupby('turma').agg({
                                'nome': 'nunique',
                                'status': ['count', lambda x: (x == 'Falta').sum()]
                            }).round(2)
                            resumo_turmas.columns = ['Qtd_Alunos', 'Total_Registros', 'Total_Faltas']
                            resumo_turmas['Taxa_Presenca'] = ((resumo_turmas['Total_Registros'] - resumo_turmas['Total_Faltas']) / resumo_turmas['Total_Registros'] * 100).round(1)
                            resumo_turmas.to_excel(writer, sheet_name='Resumo_Turmas')
                    
                    st.download_button(
                        label="📊 Baixar Relatório Excel",
                        data=output.getvalue(),
                        file_name=f"relatorio_{tipo_relatorio.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                elif formato_export == "CSV":
                    csv_output = BytesIO()
                    df_filtrado.to_csv(csv_output, index=False, encoding='utf-8')
                    
                    st.download_button(
                        label="📋 Baixar Relatório CSV",
                        data=csv_output.getvalue(),
                        file_name=f"relatorio_{tipo_relatorio.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
                    
                st.success("✅ Relatório gerado com sucesso!")
        else:
            st.warning("⚠️ Nenhum dado disponível para gerar o relatório.")

with tab5:
    st.header("🚨 Sistema de Alertas Inteligentes")
    
    # Configuração de alertas
    st.subheader("⚙️ Configuração de Alertas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        limite_falta_individual = st.slider("🎯 Limite de Faltas Individual (%)", 10, 50, 30, 5)
    with col2:
        limite_falta_turma = st.slider("🎓 Limite de Faltas por Turma (%)", 5, 30, 15, 2)
    with col3:
        dias_consecutivos = st.slider("📅 Dias Consecutivos de Falta", 2, 10, 3, 1)
    
    # Processamento de alertas
    alertas = []
    
    if not df_filtrado.empty:
        # Alerta 1: Alunos com alta taxa de faltas
        if 'nome' in df_filtrado.columns and 'turma' in df_filtrado.columns:
            alunos_alta_falta = df_filtrado.groupby(['nome', 'turma']).agg({
                'status': ['count', lambda x: (x == 'Falta').sum()]
            }).round(2)
            alunos_alta_falta.columns = ['Total_Registros', 'Total_Faltas']
            alunos_alta_falta['Percentual_Faltas'] = (alunos_alta_falta['Total_Faltas'] / alunos_alta_falta['Total_Registros'] * 100).round(1)
            alunos_criticos_alert = alunos_alta_falta[alunos_alta_falta['Percentual_Faltas'] >= limite_falta_individual].reset_index()
            
            for _, aluno in alunos_criticos_alert.iterrows():
                alertas.append({
                    'tipo': 'CRÍTICO',
                    'categoria': '👤 Aluno',
                    'titulo': f"Alta Taxa de Faltas - {aluno['nome']}",
                    'descricao': f"Aluno da turma {aluno['turma']} com {aluno['Percentual_Faltas']:.1f}% de faltas",
                    'acao': 'Contato imediato com aluno e responsáveis',
                    'prioridade': 1
                })
        
        # Alerta 2: Turmas com taxa elevada de faltas
        if 'turma' in df_filtrado.columns:
            turmas_alta_falta = df_filtrado.groupby('turma')['status'].apply(
                lambda x: (x == 'Falta').sum() / x.count() * 100
            ).reset_index(name='percentual_faltas')
            turmas_criticas = turmas_alta_falta[turmas_alta_falta['percentual_faltas'] >= limite_falta_turma]
            
            for _, turma in turmas_criticas.iterrows():
                alertas.append({
                    'tipo': 'ATENÇÃO',
                    'categoria': '🎓 Turma',
                    'titulo': f"Taxa Elevada de Faltas - Turma {turma['turma']}",
                    'descricao': f"Turma com {turma['percentual_faltas']:.1f}% de taxa de faltas",
                    'acao': 'Reunião com professores da turma',
                    'prioridade': 2
                })
        
        # Alerta 3: Tendência crescente de faltas
        if len(df_filtrado) > 30:  # Só analisa se tiver dados suficientes
            df_recente = df_filtrado[df_filtrado['data'] >= df_filtrado['data'].max() - timedelta(days=7)]
            df_anterior = df_filtrado[(df_filtrado['data'] >= df_filtrado['data'].max() - timedelta(days=14)) & 
                                    (df_filtrado['data'] < df_filtrado['data'].max() - timedelta(days=7))]
            
            if len(df_recente) > 0 and len(df_anterior) > 0:
                taxa_recente = len(df_recente[df_recente['status'] == 'Falta']) / len(df_recente) * 100
                taxa_anterior = len(df_anterior[df_anterior['status'] == 'Falta']) / len(df_anterior) * 100
                variacao = taxa_recente - taxa_anterior
                
                if variacao > 10:  # Aumento significativo
                    alertas.append({
                        'tipo': 'ATENÇÃO',
                        'categoria': '📈 Tendência',
                        'titulo': 'Aumento Significativo de Faltas',
                        'descricao': f'Aumento de {variacao:.1f}% na última semana',
                        'acao': 'Investigar causas do aumento de faltas',
                        'prioridade': 2
                    })
    
    # Exibição dos alertas
    if alertas:
        # Ordenar por prioridade
        alertas.sort(key=lambda x: x['prioridade'])
        
        st.subheader(f"🔔 Alertas Ativos ({len(alertas)})")
        
        for i, alerta in enumerate(alertas):
            cor_fundo = "#ffebee" if alerta['tipo'] == 'CRÍTICO' else "#fff3e0"
            cor_borda = "#f44336" if alerta['tipo'] == 'CRÍTICO' else "#ff9800"
            
            st.markdown(f"""
            <div style="background-color: {cor_fundo}; border-left: 4px solid {cor_borda}; padding: 1rem; margin: 0.5rem 0; border-radius: 5px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0; color: {cor_borda};">
                            {alerta['categoria']} | {alerta['titulo']}
                        </h4>
                        <p style="margin: 0.5rem 0;"><strong>Situação:</strong> {alerta['descricao']}</p>
                        <p style="margin: 0;"><strong>Ação Recomendada:</strong> {alerta['acao']}</p>
                    </div>
                    <div style="text-align: right;">
                        <span style="background-color: {cor_borda}; color: white; padding: 0.25rem 0.5rem; border-radius: 3px; font-size: 0.8rem;">
                            {alerta['tipo']}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Ações em massa
        st.subheader("🎯 Ações Recomendadas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📧 Enviar Alertas por Email", type="secondary"):
                st.info("Funcionalidade de email seria implementada aqui")
        
        with col2:
            if st.button("📱 Notificar Coordenadores", type="secondary"):
                st.info("Sistema de notificações seria implementado aqui")
        
        with col3:
            if st.button("📋 Gerar Plano de Ação", type="secondary"):
                st.info("Gerador de plano de ação seria implementado aqui")
    
    else:
        st.success("✅ Nenhum alerta ativo no momento! Sistema operando dentro dos parâmetros normais.")
        
        # Mostrar próximos marcos de atenção
        st.subheader("📊 Status do Sistema")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Status Geral", 
                "🟢 NORMAL", 
                help="Sistema operando dentro dos parâmetros estabelecidos"
            )
        
        with col2:
            proxima_revisao = datetime.now() + timedelta(days=7)
            st.metric(
                "Próxima Revisão", 
                proxima_revisao.strftime("%d/%m"),
                help="Próxima análise automática do sistema"
            )
        
        with col3:
            st.metric(
                "Alertas Resolvidos", 
                "✅ 0", 
                help="Número de alertas resolvidos hoje"
            )

# Registros recentes na parte inferior
st.markdown("---")
st.header("📋 Registros Mais Recentes")

if not df_filtrado.empty:
    # Filtros rápidos para a tabela
    col1, col2, col3 = st.columns(3)
    
    with col1:
        mostrar_apenas_faltas = st.checkbox("Mostrar apenas faltas", value=False)
    with col2:
        limite_registros = st.selectbox("Número de registros", [10, 25, 50, 100], index=0)
    with col3:
        ordenar_por = st.selectbox("Ordenar por", ["Data", "Nome", "Turma", "Status"])
    
    # Aplicar filtros
    df_tabela = df_filtrado.copy()
    
    if mostrar_apenas_faltas:
        df_tabela = df_tabela[df_tabela['status'] == 'Falta']
    
    # Ordenação
    if ordenar_por == "Data":
        df_tabela = df_tabela.sort_values('data', ascending=False)
    elif ordenar_por == "Nome":
        df_tabela = df_tabela.sort_values('nome')
    elif ordenar_por == "Turma":
        df_tabela = df_tabela.sort_values('turma')
    elif ordenar_por == "Status":
        df_tabela = df_tabela.sort_values('status')
    
    # Formatação da tabela
    colunas_disponiveis = ['data', 'nome', 'turma', 'status']
    
    # Adicionar colunas opcionais se existirem
    if 'justificativa' in df_tabela.columns:
        colunas_disponiveis.append('justificativa')
    if 'professor' in df_tabela.columns:
        colunas_disponiveis.append('professor')
    
    df_display = df_tabela[colunas_disponiveis].head(limite_registros).copy()
    df_display['data'] = df_display['data'].dt.strftime('%d/%m/%Y')
    
    # Aplicar cores condicionais
    def highlight_status(row):
        if row['status'] == 'Falta':
            return ['background-color: #ffebee'] * len(row)
        else:
            return ['background-color: #e8f5e8'] * len(row)
    
    st.dataframe(
        df_display.style.apply(highlight_status, axis=1),
        use_container_width=True,
        height=400
    )
else:
    st.info("📋 Nenhum registro de frequência encontrado para o período selecionado.")

# Footer com informações do sistema
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📊 Dashboard v2.0**")
    st.markdown("Sistema de Gestão Acadêmica")

with col2:
    st.markdown("**⏰ Última Atualização**")
    st.markdown(f"{datetime.now().strftime('%d/%m/%Y %H:%M')}")

with col3:
    st.markdown("**📈 Performance**")
    if not df_filtrado.empty:
        st.markdown(f"Processando {len(df_filtrado):,} registros")
    else:
        st.markdown("Aguardando dados")