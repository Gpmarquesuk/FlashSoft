"""
SACI v3.0 - Interface de Usuário (MVP)
======================================

Dashboard em Streamlit para interagir com a API da SACI.
"""

import streamlit as st
import requests
import pandas as pd

# URL da API do backend
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="SACI v3.0", layout="wide")

st.title("🧠 SACI v3.0 - Sistema Avançado de Convergência de Ideias")
st.caption("Uma interface para orquestrar debates entre modelos de IA.")

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
    
    if st.button("Atualizar Histórico"):
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

        df = pd.DataFrame(sorted_history)
        df_display = df[['timestamp', 'problema', 'consenso']]
        df_display.columns = ['Data', 'Debate', 'Consenso']

        st.dataframe(df_display, use_container_width=True)

        selected_debate_id = st.selectbox("Selecione um debate para ver os detalhes:", [d['debate_id'] for d in sorted_history])

        if selected_debate_id:
            with st.spinner(f"Carregando detalhes de {selected_debate_id}..."):
                details = get_debate_details(selected_debate_id)
                if details:
                    st.subheader(f"Detalhes do Debate: {details.get('problema', selected_debate_id)}")
                    
                    st.metric("Consenso Atingido?", "Sim" if details.get('consenso') else "Não")

                    if details.get('solucao_final'):
                        with st.expander("Solução Final / Síntese"):
                            st.markdown(details['solucao_final'])
                    
                    st.write("---")
                    st.subheader("Resumo das Rodadas")

                    for i, rodada in enumerate(details.get('rodadas', [])):
                        analise = rodada.get('analise_convergencia', {})
                        metodo = analise.get('metodo', 'N/A')
                        
                        if metodo == 'semantico':
                            score = analise.get('score', 0)
                            st.write(f"**Rodada {i+1}**: Convergência Semântica de `{score:.2f}`")
                        else:
                            votos = analise.get('votos', {})
                            st.write(f"**Rodada {i+1}**: Fallback por Votos - `{votos}`")

                        with st.expander(f"Ver respostas da Rodada {i+1}"):
                            for model_key, resp_data in rodada.get('respostas', {}).items():
                                st.markdown(f"**_{resp_data['model_name']}_**")
                                if resp_data['success']:
                                    st.markdown(resp_data['response'])
                                else:
                                    st.error(f"Falha ao obter resposta: {resp_data.get('error', 'Erro desconhecido')}")
                                st.markdown("---")
