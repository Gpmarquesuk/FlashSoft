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
import time
import pandas as pd
import plotly.graph_objects as go
import json
import os
from datetime import datetime

# --- Utilidades internas ---

def force_rerun() -> None:
    """Força o Streamlit a reiniciar o script, independente da versão."""
    rerun_callable = getattr(st, "experimental_rerun", None) or getattr(st, "rerun", None)
    if rerun_callable:
        rerun_callable()
        return
    try:
        from streamlit.runtime.scriptrunner import RerunException, RerunData  # type: ignore
    except ImportError:  # fallback para versões muito antigas
        from streamlit.script_runner import RerunException, RerunData  # type: ignore
    raise RerunException(RerunData())

# --- Configuração da Página e API ---
st.set_page_config(page_title="SACI - Debate ao Vivo", layout="wide")
API_URL = "http://127.0.0.1:8000"

# --- Estilos CSS Customizados ---
st.markdown("""
<style>
    /* Melhora a aparência dos cards de métricas */
    [data-testid="stMetric"] {
        background-color: #2a2a38;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    [data-testid="stMetricLabel"] {
        font-weight: bold;
        color: #a0a0b0;
    }
    [data-testid="stMetricValue"] {
        font-size: 2em;
        color: #ffffff;
    }
    /* Estilo para o container de resposta */
    .response-container {
        padding: 15px;
        border: 1px solid #444;
        border-radius: 8px;
        max-height: 600px;
        overflow-y: auto;
        background-color: #1e1e2f;
        font-family: 'Courier New', Courier, monospace;
        white-space: pre-wrap; /* Garante a quebra de linha */
        word-wrap: break-word; /* Garante a quebra de palavras longas */
    }
    .model-header {
        font-size: 1.2em;
        font-weight: bold;
        color: #3498db;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- Funções de Interação com a API ---

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
        st.error(f"❌ Erro de conexão ao iniciar debate: {e}")
        return None

def get_debate_status(debate_id):
    try:
        response = requests.get(f"{API_URL}/debates/{debate_id}/status")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Não mostra erro na tela para não poluir, mas loga no console
        print(f"Erro ao buscar status: {e}")
        return None

def get_history():
    try:
        response = requests.get(f"{API_URL}/debates")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ Erro ao carregar histórico: {e}")
        return []

# --- Funções de Renderização da UI ---

def render_side_by_side_comparison(rodada):
    respostas = rodada.get('respostas', {})
    model_order = ['claude', 'codex', 'gemini', 'grok']
    cols = st.columns(len(model_order))

    for idx, model_key in enumerate(model_order):
        if model_key in respostas:
            resp_data = respostas[model_key]
            with cols[idx]:
                st.markdown(f"<div class='model-header'>{resp_data.get('model_name', model_key.title())}</div>", unsafe_allow_html=True)
                if resp_data.get('success'):
                    st.markdown(f"<div class='response-container'>{resp_data['response']}</div>", unsafe_allow_html=True)
                else:
                    st.error(f"Erro: {resp_data.get('error', 'Desconhecido')}")

def plot_convergence_chart(rodadas):
    scores = [r.get('analise_convergencia', {}).get('score', 0) for r in rodadas if r.get('analise_convergencia', {}).get('metodo') == 'semantico']
    if not scores:
        return None
    
    threshold = rodadas[0].get('analise_convergencia', {}).get('threshold', 0.85)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=scores, mode='lines+markers', name='Convergência'))
    fig.add_hline(y=threshold, line_dash="dash", name='Threshold')
    fig.update_layout(
        title='Evolução da Convergência Semântica',
        yaxis_range=[0,1],
        template='plotly_dark'
    )
    return fig

def live_debate_view(debate_id):
    # Busca informações iniciais do debate para exibir título apropriado
    initial_status = get_debate_status(debate_id)
    debate_title = initial_status.get('problema', debate_id) if initial_status else debate_id
    if len(debate_title) > 80:
        debate_title = debate_title[:80] + "..."
    
    # BOTÃO DE VOLTAR SEMPRE NO TOPO
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("⬅️ Voltar"):
            st.session_state.view = 'main'
            force_rerun()
            return
    with col2:
        st.header(f"🔴 {debate_title}")
    
    # Busca o status do debate
    status_data = get_debate_status(debate_id)

    if not status_data or 'error' in status_data:
        st.error("❌ Não foi possível obter o status do debate. Verifique se o backend está rodando.")
        st.caption(f"🕒 Última tentativa: {datetime.now().strftime('%H:%M:%S')}")
        return

    st.caption(f"🕒 Última atualização: {datetime.now().strftime('%H:%M:%S')}")

    rodada_atual = status_data.get('rodada_atual', 0)
    max_rodadas = status_data.get('max_rodadas', 0)
    rodadas = status_data.get('rodadas', []) or []
    solucao = status_data.get('solucao_final')
    consenso = status_data.get('consenso')
    is_finished = consenso is not None

    st.subheader("Visão Geral")
    cols = st.columns(4)
    cols[0].metric("Rodada Atual", f"{rodada_atual} / {max_rodadas}")
    cols[1].metric("Status", "🏁 Finalizado" if is_finished else "🏃 Em Andamento")
    if is_finished:
        if consenso:
            cols[2].success("✅ Consenso Atingido")
        else:
            cols[2].error("❌ Sem Consenso")
    else:
        cols[2].info("⏳ Aguardando Consenso")

    if not is_finished:
        progresso = rodada_atual / max(max_rodadas, 1)
        st.progress(progresso)

    if solucao:
        st.success("#### 💡 Solução Consensual Encontrada:")
        with st.expander("📖 Ver Solução Completa", expanded=True):
            st.markdown(solucao)

    if rodadas:
        fig = plot_convergence_chart(rodadas)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detalhes das Rodadas")
    if rodadas:
        for rodada in reversed(rodadas):
            expanded = rodada['numero'] == rodada_atual or (is_finished and rodada['numero'] == len(rodadas))
            with st.expander(f"Rodada {rodada['numero']}", expanded=expanded):
                render_side_by_side_comparison(rodada)
    else:
        st.info("Aguardando início da primeira rodada...")

    if is_finished:
        if not st.session_state.get(f"balloons_{debate_id}"):
            st.session_state[f"balloons_{debate_id}"] = True
            st.balloons()
        st.success("✅ Debate finalizado!")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Novo Debate"):
                st.session_state.view = 'main'
                st.session_state.pop('debate_id', None)
                force_rerun()
        with col2:
            if st.button("📚 Ver Histórico"):
                st.session_state.view = 'main'
                st.session_state.pop('debate_id', None)
                force_rerun()
    else:
        # Auto-refresh apenas para debates em andamento, com intervalo maior
        st.caption("🔄 Página será atualizada automaticamente em 3 segundos...")
        time.sleep(3)
        force_rerun()

def main_view():
    st.title("🧠 SACI - Sistema Avançado de Convergência de Ideias")
    
    tab1, tab2 = st.tabs(["🚀 Novo Debate", "📚 Histórico"])

    with tab1:
        st.header("Iniciar um Novo Debate")
        with st.form("debate_form"):
            problema = st.text_area("Problema Central", "Qual a melhor abordagem para...")
            contexto = st.text_area("Contexto Adicional", "Considere os seguintes fatores...")
            
            col1, col2 = st.columns(2)
            max_rodadas = col1.number_input("Máximo de Rodadas", 1, 10, 3)
            debug_mode = col2.checkbox("Modo Debug (Modelos Gratuitos)", True)
            
            if st.form_submit_button("▶️ Iniciar e Acompanhar ao Vivo"):
                result = start_debate(problema, contexto, max_rodadas, debug_mode)
                if result and 'debate_id' in result:
                    st.session_state.view = 'live'
                    st.session_state.debate_id = result['debate_id']
                    force_rerun()
                    return 'live'
                else:
                    st.error("Não foi possível iniciar o debate. Verifique o console do servidor.")

    with tab2:
        st.header("Histórico de Debates")
        st.button("🔄 Atualizar Histórico")  # clique dispara rerun automático
            
        history = get_history()
        if history:
            # Mapeia o problema ao ID para uma seleção mais amigável
            # Adiciona timestamp para melhor identificação
            debate_options = {}
            for d in sorted(history, key=lambda x: x.get('timestamp', 0), reverse=True):
                dt = datetime.fromtimestamp(d.get('timestamp', 0)).strftime('%d/%m/%Y %H:%M')
                label = f"[{dt}] - {d.get('problema', 'Problema desconhecido')}"
                debate_options[label] = d['debate_id']

            selected_label = st.selectbox("Selecione um debate para ver os detalhes:", options=list(debate_options.keys()))
            
            if selected_label:
                selected_id = debate_options[selected_label]
                # Aqui você pode adicionar a lógica para mostrar detalhes de um debate histórico
                st.info(f"Detalhes para {selected_id} ainda não implementado nesta visualização.")
        else:
            st.info("Nenhum debate no histórico.")


# --- Lógica Principal de Navegação ---
if 'view' not in st.session_state:
    st.session_state.view = 'main'

if st.session_state.view == 'live':
    live_debate_view(st.session_state.debate_id)
else:
    next_view = main_view()
    if next_view == 'live':
        live_debate_view(st.session_state.debate_id)
