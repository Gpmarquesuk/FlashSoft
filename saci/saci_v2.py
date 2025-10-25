#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SACI v2.1 - Sistema Avançado de Convergência de Ideias (EVOLUÍDA)
=================================================================

DEFINIÇÃO:
----------
SACI v2.1 combina o debate multi-agente da v1.0 com análise de convergência
semântica usando embeddings, conforme decidido pela própria SACI.

ARQUITETURA:
------------
1.  **Debate Multi-Agente:** 4 modelos oficiais (Claude, GPT-5, Gemini, Grok)
    debatem o problema em rodadas, como na v1.0.
2.  **Análise Semântica:** Ao final de cada rodada, as respostas são convertidas
    em vetores de embedding usando a API da OpenAI.
3.  **Métrica de Convergência:** A similaridade de cosseno entre os vetores é
    calculada. Se a similaridade média ultrapassar um threshold, o debate
    termina (early stopping).
4.  **Fallback:** Se a API de embeddings falhar, o sistema reverte para a
    contagem de votos por palavra-chave da v1.0 para aquela rodada.

FLUXO:
------
1. Inicia o debate.
2. Para cada rodada:
   a. Coleta respostas dos 4 modelos.
   b. Tenta gerar embeddings e calcular a convergência semântica.
   c. Se sucesso e convergência > threshold -> FIM.
   d. Se falha na API de embeddings -> Usa o parser de votos da v1.0.
   e. Se consenso por votos -> FIM.
3. Se não houver consenso, continua para a próxima rodada.
4. Ao final, sintetiza a solução.

Autor: FlashSoft Team
Data: 24/10/2025
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Clientes de LLM
from llm_client import chat
from embedding_client import get_embedding

# Utilitários
from numpy import dot
from numpy.linalg import norm
import numpy as np

# ============================================================================
# CONFIGURAÇÃO DE MODELOS
# ============================================================================

# Modelos de Produção (Pagos)
SACI_MODELS_PROD = {
    'claude': {
        'id': 'anthropic/claude-sonnet-4.5',
        'name': 'Claude Sonnet 4.5'
    },
    'codex': {
        'id': 'openai/gpt-5-codex',
        'name': 'GPT-5 Codex'
    },
    'gemini': {
        'id': 'google/gemini-2.5-pro',
        'name': 'Gemini 2.5 PRO'
    },
    'grok': {
        'id': 'x-ai/grok-4',
        'name': 'Grok 4'
    }
}

# Modelos de Debug (Gratuitos)
SACI_MODELS_FREE = {
    'claude': {
        'id': 'z-ai/glm-4.5-air:free',
        'name': 'GLM 4.5 Air (Free)'
    },
    'codex': {
        'id': 'qwen/qwen-2.5-coder-32b-instruct:free',
        'name': 'Qwen Coder (Free)'
    },
    'gemini': {
        'id': 'tngtech/deepseek-r1t2-chimera:free',
        'name': 'Chimera (Free)'
    },
    'grok': {
        'id': 'meta-llama/llama-3.3-8b-instruct:free',
        'name': 'Llama 3.3 8B (Free)'
    }
}

DELAY_BETWEEN_CALLS = 2  # segundos
SEMANTIC_CONVERGENCE_THRESHOLD = 0.85  # Threshold de similaridade de cosseno

# ============================================================================
# FUNÇÕES DE CORE
# ============================================================================

def debate_saci_v2(
    problema: str,
    contexto: str = "",
    max_rodadas: int = 3,
    output_dir: str = "logs",
    verbose: bool = True,
    debug_mode: bool = False
) -> Dict:
    """
    Executa um debate SACI v2.1 completo com análise semântica.
    
    Args:
        problema: Questão/problema a ser debatido.
        contexto: Contexto adicional relevante.
        max_rodadas: Número máximo de rodadas de debate.
        output_dir: Diretório para salvar logs.
        verbose: Imprimir progresso no console.
        debug_mode: Se True, usa modelos gratuitos para depuração.
        
    Returns:
        Dict com o resultado completo do debate.
    """
    
    saci_models = SACI_MODELS_FREE if debug_mode else SACI_MODELS_PROD
    
    if verbose:
        print("\n" + "="*80)
        print(f"🚀 SACI v2.1 (EVOLUÍDA) - DEBATE INICIADO {'(MODO DEBUG)' if debug_mode else ''}")
        print("="*80)
        print(f"\n📋 Problema: {problema[:100]}...")
        print(f"🎯 Convergência Semântica: {SEMANTIC_CONVERGENCE_THRESHOLD*100}%")
        print(f"🔄 Max rodadas: {max_rodadas}\n")

    os.makedirs(output_dir, exist_ok=True)
    
    historico = []
    consenso_atingido = False
    solucao_final = None
    
    for rodada_num in range(1, max_rodadas + 1):
        if verbose:
            print(f"\n{'='*80}")
            print(f"🔄 RODADA {rodada_num}/{max_rodadas}")
            print(f"{'='*80}\n")
        
        # 1. Coletar respostas
        prompt = _build_prompt(problema, contexto, historico)
        
        start_time = time.time()
        respostas = _collect_responses(prompt, verbose, saci_models)
        end_time = time.time()
        
        if verbose:
            print(f"\n⏱️  Tempo da rodada de consultas: {end_time - start_time:.2f} segundos (paralelizado)")
        
        rodada_data = {
            'numero': rodada_num,
            'respostas': respostas,
            'timestamp': datetime.now().isoformat(),
            'analise_convergencia': {}
        }
        
        # 2. Análise de Convergência
        try:
            convergence_score, all_embeddings = _calculate_semantic_convergence(respostas)
            rodada_data['analise_convergencia'] = {
                'score': convergence_score,
                'threshold': SEMANTIC_CONVERGENCE_THRESHOLD,
                'metodo': 'semantico'
            }
            if verbose:
                print(f"\n📈 Convergência Semântica da Rodada: {convergence_score:.2f}")

            if convergence_score >= SEMANTIC_CONVERGENCE_THRESHOLD:
                consenso_atingido = True
                solucao_final = _synthesize_solution(respostas, "Consenso Semântico")
                if verbose:
                    print(f"✅ CONSENSO SEMÂNTICO ATINGIDO!")
        
        except Exception as e:
            if verbose:
                print(f"\n⚠️ Falha na análise semântica: {e}")
                print("   Revertendo para análise de votos por keyword (fallback)...")
            
            # Fallback para v1.0
            votos = _extract_votes_fallback(respostas)
            rodada_data['analise_convergencia'] = {
                'votos': votos,
                'metodo': 'keyword_fallback'
            }
            consenso_atingido, solucao_final = _check_consensus_fallback(votos, 0.75, respostas, len(saci_models))
            if verbose:
                print(f"📊 Votos (Fallback): {votos}")
            if consenso_atingido:
                 if verbose:
                    print(f"✅ CONSENSO POR VOTOS (FALLBACK) ATINGIDO!")

        historico.append(rodada_data)
        
        if consenso_atingido:
            break

    # Resultado Final
    resultado = {
        'consenso': consenso_atingido,
        'solucao_final': solucao_final,
        'rodadas': historico,
        'timestamp': datetime.now().isoformat(),
        'versao': '2.1',
        'debug_mode': debug_mode
    }
    
    log_filename = f"{output_dir}/saci_v2_debate_{int(time.time())}.json"
    with open(log_filename, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
        
    if verbose:
        print(f"\n{'='*80}")
        print("📁 DEBATE FINALIZADO (v2.1)")
        print(f"{'='*80}")
        print(f"✅ Consenso: {'SIM' if consenso_atingido else 'NÃO'}")
        print(f"📄 Log salvo: {log_filename}\n")

    return resultado

# ============================================================================
# FUNÇÕES DE LÓGICA DE DEBATE
# ============================================================================

def _collect_responses(prompt: str, verbose: bool, saci_models: Dict) -> Dict:
    """Coleta respostas de todos os modelos SACI em paralelo."""
    respostas = {}
    with ThreadPoolExecutor(max_workers=len(saci_models)) as executor:
        future_to_model = {
            executor.submit(
                _fetch_single_response, 
                model_info['id'], 
                prompt, 
                model_info['name']
            ): model_key
            for model_key, model_info in saci_models.items()
        }

        for future in as_completed(future_to_model):
            model_key = future_to_model[future]
            model_name = saci_models[model_key]['name']
            if verbose:
                print(f"⏳ Coletando resposta de {model_name}...")
            try:
                respostas[model_key] = future.result()
                if verbose:
                    print(f"✅ {model_name}: {len(respostas[model_key]['response'])} chars")
            except Exception as e:
                if verbose:
                    print(f"❌ {model_name}: ERROR - {e}")
                respostas[model_key] = {
                    'model_name': model_name,
                    'response': None,
                    'success': False,
                    'error': str(e)
                }
    return respostas

def _fetch_single_response(model_id: str, prompt: str, model_name: str) -> Dict:
    """Função auxiliar para buscar uma única resposta de um modelo."""
    response_text = chat(
        model=model_id,
        system="You are an expert AI participant in a structured debate.",
        user=prompt,
        temperature=0.4,
        max_tokens=10000
    )
    return {
        'model_name': model_name,
        'response': response_text,
        'success': True
    }

def _calculate_semantic_convergence(respostas: Dict) -> tuple[float, Dict]:
    """Gera embeddings e calcula a similaridade de cosseno média."""
    embeddings = {}
    valid_responses = [r['response'] for r in respostas.values() if r['success'] and r['response']]
    
    if len(valid_responses) < 2:
        return 0.0, {}

    with ThreadPoolExecutor(max_workers=len(valid_responses)) as executor:
        future_to_key = {
            executor.submit(get_embedding, resp_data['response']): key
            for key, resp_data in respostas.items() if resp_data['success'] and resp_data['response']
        }
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                embeddings[key] = future.result()
            except Exception as e:
                print(f"Falha ao gerar embedding para {key}: {e}")


    # Calcular similaridade de cosseno par a par
    keys = list(embeddings.keys())
    scores = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            vec1 = np.array(embeddings[keys[i]])
            vec2 = np.array(embeddings[keys[j]])
            
            # Normalizar vetores para evitar divisão por zero
            if norm(vec1) > 0 and norm(vec2) > 0:
                cosine_sim = dot(vec1, vec2) / (norm(vec1) * norm(vec2))
                scores.append(cosine_sim)

    if not scores:
        return 0.0, embeddings

    return np.mean(scores), embeddings

def _synthesize_solution(respostas: Dict, reason: str) -> str:
    """Cria uma solução final a partir das respostas."""
    synthesis = f"Consenso Atingido por {reason}.\n\n"
    synthesis += "Síntese das propostas convergentes:\n"
    
    # Idealmente, usar um LLM para sintetizar, mas por enquanto, concatenamos
    for key, resp_data in respostas.items():
        if resp_data['success']:
            synthesis += f"\n--- {resp_data['model_name']} ---\n"
            synthesis += resp_data['response'][:500] + "...\n"
            
    return synthesis

# ============================================================================
# PROMPT BUILDERS E FALLBACKS (Adaptados da v1.0)
# ============================================================================

def _build_prompt(problema: str, contexto: str, historico: List[Dict]) -> str:
    """Constrói o prompt para a rodada atual."""
    if not historico: # Rodada 1
        return f"""# DEBATE SACI v2.1 - RODADA 1
        ## PROBLEMA: {problema}
        ## CONTEXTO: {contexto or 'N/A'}
        ## SUA TAREFA: Analise, proponha uma solução e justifique.
        ## FORMATO: Análise, Proposta, Voto (se aplicável), Justificativa."""
    else: # Rodadas seguintes
        rodada_num = len(historico) + 1
        ultima_rodada = historico[-1]
        prompt = f"# DEBATE SACI v2.1 - RODADA {rodada_num}\n\n## RESUMO DA RODADA ANTERIOR:\n"
        for model, resp in ultima_rodada['respostas'].items():
            if resp['success']:
                prompt += f"\n- {resp['model_name']}: {resp['response'][:300]}...\n"
        prompt += "\n## SUA TAREFA: Avalie, refine sua posição e busque o consenso."
        return prompt

def _extract_votes_fallback(respostas: Dict) -> Dict:
    """Fallback para extrair votos por keyword, igual à v1.0."""
    import re
    votos = {}
    for model_key, resp_data in respostas.items():
        voto = "unclear"
        if resp_data['success']:
            try:
                response_lower = resp_data['response'].lower()
                patterns = [r'\*\*voto:\s*([a-e])\*\*', r'voto:\s*([a-e])']
                for p in patterns:
                    match = re.search(p, response_lower)
                    if match:
                        voto = match.group(1).upper()
                        break
            except Exception:
                pass
        votos[model_key] = voto
    return votos

def _check_consensus_fallback(votos: Dict, threshold: float, respostas: Dict, total_modelos: int) -> tuple:
    """Fallback para checar consenso por votos, igual à v1.0."""
    if not votos: return False, None
    contagem = {}
    for voto in votos.values(): contagem[voto] = contagem.get(voto, 0) + 1
    
    total_votos_validos = len([v for v in votos.values() if v != 'unclear'])
    if total_votos_validos == 0: return False, None

    voto_majoritario = max(contagem, key=contagem.get)
    if voto_majoritario == 'unclear' and len(contagem) > 1:
        del contagem['unclear']
        voto_majoritario = max(contagem, key=contagem.get)

    qtd_majoritaria = contagem.get(voto_majoritario, 0)
    
    if (qtd_majoritaria / total_modelos) >= threshold:
        solucao = f"Consenso (Fallback): {voto_majoritario} ({qtd_majoritaria}/{total_modelos})"
        return True, solucao
    
    return False, None

# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Instalar dependências se necessário
    try:
        import numpy
    except ImportError:
        print("Instalando numpy...")
        os.system("pip install numpy")

    problema_exemplo = "Qual a melhor abordagem para modernizar um sistema legado: reescrever do zero (big bang) ou refatoração incremental (strangler fig)?"
    contexto_exemplo = "Sistema: Monolito em COBOL. Equipe: 5 desenvolvedores sêniores. Risco: Alto, sistema crítico para a operação."

    debate_saci_v2(
        problema=problema_exemplo,
        contexto=contexto_exemplo,
        verbose=True
    )
