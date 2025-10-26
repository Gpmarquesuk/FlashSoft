"""
SACI v3.1 - Interface de Usuário (EVOLUÍDA)
===========================================

Dashboard em Streamlit com visualizações avançadas:
- Gráficos de convergência semântica
- Comparativo lado-a-lado de respostas
- Exportação de debates
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# URL da API do backend
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="SACI v3.1", layout="wide")

st.title("🧠 SACI v3.1 - Sistema Avançado de Convergência de Ideias")
st.caption("Interface evoluída com visualizações e análises comparativas.")

# ============================================================================
# Funções da API
# ============================================================================

def start_debate(problema, contexto, max_rodadas, debug_mode):
    payload = {
        "problema": problema,
        "contexto": contexto,
        "max_rodadas": max_rodadas,
        "debug_mode": debug_mode
    }
    try:
        response = requests.post(f"{API_URL}/debates", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao iniciar debate: {e}")
        return None

def get_history():
    try:
        response = requests.get(f"{API_URL}/debates")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao carregar histórico: {e}")
        return []

def get_debate_details(debate_id):
    try:
        response = requests.get(f"{API_URL}/debates/{debate_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao carregar detalhes do debate: {e}")
        return None

# ============================================================================
# Funções de Visualização
# ============================================================================

def plot_convergence_chart(rodadas):
    """Cria gráfico de linha mostrando a evolução da convergência semântica."""
    rodada_nums = []
    convergence_scores = []
    
    for rodada in rodadas:
        analise = rodada.get('analise_convergencia', {})
        if analise.get('metodo') == 'semantico':
            rodada_nums.append(rodada['numero'])
            convergence_scores.append(analise.get('score', 0))
    
    if not rodada_nums:
        return None
    
    fig = go.Figure()
    
    # Linha de convergência
    fig.add_trace(go.Scatter(
        x=rodada_nums,
        y=convergence_scores,
        mode='lines+markers',
        name='Convergência Semântica',
        line=dict(color='#3498db', width=3),
        marker=dict(size=10)
    ))
    
    # Linha de threshold
    threshold = rodadas[0].get('analise_convergencia', {}).get('threshold', 0.85)
    fig.add_trace(go.Scatter(
        x=rodada_nums,
        y=[threshold] * len(rodada_nums),
        mode='lines',
        name=f'Threshold ({threshold:.0%})',
        line=dict(color='#e74c3c', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='Evolução da Convergência Semântica',
        xaxis_title='Rodada',
        yaxis_title='Score de Convergência',
        yaxis=dict(range=[0, 1], tickformat='.0%'),
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def render_side_by_side_comparison(rodada):
    """Renderiza respostas dos modelos lado a lado em colunas."""
    respostas = rodada.get('respostas', {})
    
    # Ordem fixa dos modelos
    model_order = ['claude', 'codex', 'gemini', 'grok']
    cols = st.columns(4)
    
    for idx, model_key in enumerate(model_order):
        if model_key not in respostas:
            continue
            
        resp_data = respostas[model_key]
        with cols[idx]:
            st.markdown(f"**{resp_data['model_name']}**")
            
            if resp_data['success']:
                # Truncar resposta para economizar espaço
                response_text = resp_data['response']
                if len(response_text) > 500:
                    response_text = response_text[:500] + "..."
                    
                st.markdown(
                    f"<div style='padding: 10px; border: 1px solid #ddd; border-radius: 5px; height: 300px; overflow-y: auto;'>"
                    f"{response_text}"
                    f"</div>",
                    unsafe_allow_html=True
                )
                
                with st.expander("Ver resposta completa"):
                    st.markdown(resp_data['response'])
            else:
                st.error(f"❌ {resp_data.get('error', 'Erro desconhecido')}")

def export_debate_markdown(details):
    """Gera markdown formatado do debate para download."""
    md = f"# Debate SACI v3.1\n\n"
    md += f"**Problema:** {details.get('problema', 'N/A')}\n\n"
    md += f"**Consenso Atingido:** {'✅ Sim' if details.get('consenso') else '❌ Não'}\n\n"
    md += f"**Data:** {details.get('timestamp', 'N/A')}\n\n"
    
    if details.get('solucao_final'):
        md += f"## Solução Final\n\n{details['solucao_final']}\n\n"
    
    md += "## Rodadas de Debate\n\n"
    
    for rodada in details.get('rodadas', []):
        md += f"### Rodada {rodada['numero']}\n\n"
        analise = rodada.get('analise_convergencia', {})
        if analise.get('metodo') == 'semantico':
            md += f"**Convergência:** {analise.get('score', 0):.2%}\n\n"
        
        for model_key, resp_data in rodada.get('respostas', {}).items():
            md += f"#### {resp_data['model_name']}\n\n"
            if resp_data['success']:
                md += f"{resp_data['response']}\n\n"
            else:
                md += f"*Erro: {resp_data.get('error', 'Desconhecido')}*\n\n"
        
        md += "---\n\n"
    
    return md

# ============================================================================
# Layout da UI
# ============================================================================

tab1, tab2 = st.tabs(["🚀 Novo Debate", "📚 Histórico"])

# --- Aba de Novo Debate ---
with tab1:
    st.header("Iniciar um Novo Debate")
    
    with st.form("debate_form"):
        problema = st.text_area("Problema Central", "Qual a melhor abordagem para...")
        contexto = st.text_area("Contexto Adicional", "Considere os seguintes fatores...")
        
        col1, col2 = st.columns(2)
        with col1:
            max_rodadas = st.number_input("Máximo de Rodadas", min_value=1, max_value=10, value=3)
        with col2:
            debug_mode = st.checkbox("Modo Debug (Modelos Gratuitos)", value=False)
            
        submitted = st.form_submit_button("Iniciar Debate")
        
        if submitted:
            with st.spinner("Enviando requisição para o servidor SACI..."):
                result = start_debate(problema, contexto, max_rodadas, debug_mode)
                if result:
                    st.success(result['message'])
                    st.info("Acompanhe o progresso na aba 'Histórico'.")

# --- Aba de Histórico ---
with tab2:
    st.header("Histórico de Debates")
    
    # Filtros e Busca
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_text = st.text_input("🔍 Buscar no problema", "")
    with col2:
        filter_consenso = st.selectbox("Consenso", ["Todos", "Sim", "Não"])
    with col3:
        filter_modo = st.selectbox("Modo", ["Todos", "Produção", "Debug"])
    with col4:
        if st.button("🔄 Atualizar"):
            st.rerun()

    history_data = get_history()
    
    if not history_data:
        st.info("Nenhum debate encontrado. Inicie um na aba 'Novo Debate'.")
    else:
        # Ordenar por timestamp
        for item in history_data:
            try:
                ts_from_id = int(item['debate_id'].split('_')[-1].split('.')[0])
                item['sort_key'] = ts_from_id
            except (ValueError, IndexError):
                item['sort_key'] = 0
        
        sorted_history = sorted(history_data, key=lambda x: x['sort_key'], reverse=True)
        
        # Aplicar filtros
        filtered_history = sorted_history
        
        # Filtro de busca de texto
        if search_text:
            filtered_history = [d for d in filtered_history if search_text.lower() in d['problema'].lower()]
        
        # Filtro de consenso
        if filter_consenso != "Todos":
            consenso_bool = (filter_consenso == "Sim")
            filtered_history = [d for d in filtered_history if d['consenso'] == consenso_bool]
        
        # Filtro de modo (precisa carregar detalhes do debate)
        # Nota: Este filtro pode ser lento se houver muitos debates
        # Uma otimização seria adicionar 'debug_mode' diretamente ao DebateInfo
        
        if not filtered_history:
            st.warning("Nenhum debate encontrado com os filtros aplicados.")
        else:
            st.success(f"Mostrando {len(filtered_history)} de {len(sorted_history)} debates")
            
            df = pd.DataFrame(filtered_history)
            df_display = df[['timestamp', 'problema', 'consenso']]
            df_display.columns = ['Data', 'Debate', 'Consenso']

            st.dataframe(df_display, use_container_width=True)

            selected_debate_id = st.selectbox("Selecione um debate para ver os detalhes:", [d['debate_id'] for d in filtered_history])

            if selected_debate_id:
                with st.spinner(f"Carregando detalhes de {selected_debate_id}..."):
                    details = get_debate_details(selected_debate_id)
                    if details:
                        # Header com métricas
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Consenso Atingido?", "✅ Sim" if details.get('consenso') else "❌ Não")
                        with col2:
                            st.metric("Rodadas", len(details.get('rodadas', [])))
                        with col3:
                            versao = details.get('versao', 'N/A')
                            debug = "🐛 Debug" if details.get('debug_mode') else "🚀 Produção"
                            st.metric("Versão / Modo", f"{versao} ({debug})")
                        
                        # Gráfico de Convergência
                        st.write("---")
                        st.subheader("📈 Evolução da Convergência Semântica")
                        fig = plot_convergence_chart(details.get('rodadas', []))
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Nenhum dado de convergência semântica disponível (fallback de votos usado).")
                        
                        # Solução Final
                        if details.get('solucao_final'):
                            st.write("---")
                            st.subheader("💡 Solução Final / Síntese")
                            with st.expander("Ver Consenso Completo", expanded=True):
                                st.markdown(details['solucao_final'])
                        
                        # Comparativo Lado a Lado
                        st.write("---")
                        st.subheader("🔍 Análise Comparativa por Rodada")
                        
                        for i, rodada in enumerate(details.get('rodadas', [])):
                            analise = rodada.get('analise_convergencia', {})
                            metodo = analise.get('metodo', 'N/A')
                            
                            rodada_header = f"**Rodada {i+1}**"
                            if metodo == 'semantico':
                                score = analise.get('score', 0)
                                rodada_header += f" - Convergência: `{score:.2%}`"
                            else:
                                votos = analise.get('votos', {})
                                rodada_header += f" - Fallback por Votos: `{votos}`"
                            
                            st.markdown(rodada_header)
                            
                            with st.expander(f"Ver Comparativo de Respostas - Rodada {i+1}", expanded=(i==0)):
                                render_side_by_side_comparison(rodada)
                            
                            st.write("")
                        
                        # Exportação
                        st.write("---")
                        st.subheader("💾 Exportar Debate")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            markdown_content = export_debate_markdown(details)
                            st.download_button(
                                label="📄 Download em Markdown",
                                data=markdown_content,
                                file_name=f"{selected_debate_id.replace('.json', '')}.md",
                                mime="text/markdown"
                            )
                        with col2:
                            import json
                            json_content = json.dumps(details, indent=2, ensure_ascii=False)
                            st.download_button(
                                label="📊 Download em JSON",
                                data=json_content,
                                file_name=selected_debate_id,
                                mime="application/json"
                            )
