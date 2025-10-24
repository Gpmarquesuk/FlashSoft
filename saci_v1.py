#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SACI v1.0 - Sistema Avançado de Convergência de Ideias
========================================================

VERSÃO OFICIAL E ESTÁVEL para uso em produção.

DEFINIÇÃO:
----------
SACI = 4 modelos específicos de IA que debatem até obter consenso majoritário (3/4).

MODELOS OFICIAIS (NÃO ALTERAR):
---------------------------------
1. Claude Sonnet 4.5  (anthropic/claude-sonnet-4.5)
2. GPT-5 Codex        (openai/gpt-5-codex)
3. Gemini 2.5 PRO     (google/gemini-2.5-pro)
4. Grok 4             (x-ai/grok-4)

USO:
----
    from saci_v1 import debate_saci
    
    problema = "Qual banco de dados usar: PostgreSQL ou MongoDB?"
    contexto = "Sistema de e-commerce com transações críticas..."
    
    resultado = debate_saci(
        problema=problema,
        contexto=contexto,
        max_rodadas=3
    )
    
    print(f"Consenso: {resultado['consenso']}")
    print(f"Solução: {resultado['solucao_final']}")

ROADMAP:
--------
- SACI v1.0: Versão atual (estável, sem métricas quantitativas)
- SACI v2.0: SACI EVOLUÍDA (em desenvolvimento no diretório saci/)
  - Métricas de convergência semântica
  - Early stopping inteligente
  - Rastreabilidade JSON completa

QUANDO MIGRAR PARA v2.0:
------------------------
Apenas quando SACI v2.0 demonstrar superioridade comprovada em testes reais.
Até lá, USE SACI v1.0 para todos os debates de produção.

Autor: FlashSoft Team
Data: 24/10/2025
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from llm_client import chat

# ============================================================================
# CONFIGURAÇÃO OFICIAL DA SACI v1.0
# ============================================================================

SACI_MODELS = {
    'claude': {
        'id': 'anthropic/claude-sonnet-4.5',
        'name': 'Claude Sonnet 4.5',
        'specialty': 'System architecture, technical analysis'
    },
    'codex': {
        'id': 'openai/gpt-5-codex',
        'name': 'GPT-5 Codex',
        'specialty': 'Code design, implementation patterns'
    },
    'gemini': {
        'id': 'google/gemini-2.5-pro',
        'name': 'Gemini 2.5 PRO',
        'specialty': 'Strategic analysis, trade-off evaluation'
    },
    'grok': {
        'id': 'x-ai/grok-4',
        'name': 'Grok 4',
        'specialty': 'Critical thinking, edge case analysis'
    }
}

DELAY_BETWEEN_CALLS = 2  # segundos

# ============================================================================
# FUNÇÕES PRINCIPAIS
# ============================================================================

def debate_saci(
    problema: str,
    contexto: str = "",
    max_rodadas: int = 3,
    threshold_consenso: float = 0.75,
    output_dir: str = "logs",
    verbose: bool = True
) -> Dict:
    """
    Executa um debate SACI v1.0 completo.
    
    Args:
        problema: Questão/problema a ser debatido
        contexto: Contexto adicional relevante
        max_rodadas: Número máximo de rodadas de debate
        threshold_consenso: % de concordância necessária (0.75 = 3/4)
        output_dir: Diretório para salvar logs
        verbose: Imprimir progresso no console
        
    Returns:
        Dict com:
        - consenso: bool (True se atingiu consenso)
        - solucao_final: str (solução consensual ou síntese)
        - votos: Dict (distribuição de votos)
        - rodadas: List (histórico completo)
        - timestamp: str
    """
    
    if verbose:
        print("\n" + "="*80)
        print("🧠 SACI v1.0 - DEBATE INICIADO")
        print("="*80)
        print(f"\n📋 Problema: {problema[:100]}...")
        print(f"🎯 Threshold: {threshold_consenso*100}% ({int(threshold_consenso*4)}/4 modelos)")
        print(f"🔄 Max rodadas: {max_rodadas}\n")
    
    os.makedirs(output_dir, exist_ok=True)
    
    historico = []
    consenso_atingido = False
    solucao_final = None
    
    # RODADAS DE DEBATE
    for rodada_num in range(1, max_rodadas + 1):
        if verbose:
            print(f"\n{'='*80}")
            print(f"🔄 RODADA {rodada_num}/{max_rodadas}")
            print(f"{'='*80}\n")
        
        rodada_data = {
            'numero': rodada_num,
            'respostas': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Construir prompt da rodada
        if rodada_num == 1:
            prompt = _build_initial_prompt(problema, contexto)
        else:
            prompt = _build_followup_prompt(problema, contexto, historico)
        
        # Consultar cada modelo
        for model_key, model_info in SACI_MODELS.items():
            if verbose:
                print(f"⏳ Consultando {model_info['name']}...")
            
            try:
                response = chat(
                    model=model_info['id'],
                    system=f"You are an expert in {model_info['specialty']}. Participate in structured debate with other AI models to reach consensus.",
                    user=prompt,
                    temperature=0.4,
                    max_tokens=2000
                )
                
                rodada_data['respostas'][model_key] = {
                    'model_name': model_info['name'],
                    'model_id': model_info['id'],
                    'response': response,
                    'success': True
                }
                
                if verbose:
                    print(f"✅ {model_info['name']}: {len(response)} chars")
                
            except Exception as e:
                if verbose:
                    print(f"❌ {model_info['name']}: ERROR - {e}")
                
                rodada_data['respostas'][model_key] = {
                    'model_name': model_info['name'],
                    'model_id': model_info['id'],
                    'response': None,
                    'success': False,
                    'error': str(e)
                }
            
            # Delay entre chamadas
            if model_key != list(SACI_MODELS.keys())[-1]:
                time.sleep(DELAY_BETWEEN_CALLS)
        
        historico.append(rodada_data)
        
        # VERIFICAR CONSENSO
        votos = _extract_votes(rodada_data['respostas'])
        consenso_atingido, solucao_final = _check_consensus(
            votos, 
            threshold_consenso,
            rodada_data['respostas']
        )
        
        if verbose:
            print(f"\n📊 Votos da rodada {rodada_num}: {votos}")
        
        if consenso_atingido:
            if verbose:
                print(f"✅ CONSENSO ATINGIDO!")
            break
    
    # RESULTADO FINAL
    resultado = {
        'consenso': consenso_atingido,
        'solucao_final': solucao_final,
        'votos': votos if consenso_atingido else {},
        'rodadas': historico,
        'timestamp': datetime.now().isoformat(),
        'versao': '1.0'
    }
    
    # Salvar log
    log_filename = f"{output_dir}/saci_debate_{int(time.time())}.json"
    with open(log_filename, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    
    if verbose:
        print(f"\n{'='*80}")
        print("📁 DEBATE FINALIZADO")
        print(f"{'='*80}")
        print(f"✅ Consenso: {'SIM' if consenso_atingido else 'NÃO'}")
        print(f"📄 Log salvo: {log_filename}\n")
    
    return resultado


def _build_initial_prompt(problema: str, contexto: str) -> str:
    """Constrói prompt da primeira rodada."""
    return f"""# DEBATE SACI v1.0 - RODADA 1

## PROBLEMA A RESOLVER:
{problema}

## CONTEXTO:
{contexto if contexto else "N/A"}

## SUA TAREFA:
1. Analise o problema apresentado
2. Proponha uma solução clara e justificada
3. Ao final, vote em UMA opção (se houver opções explícitas) ou proponha sua própria solução
4. Seja técnico, objetivo e conciso

## FORMATO DE RESPOSTA:
- Análise: [sua análise]
- Proposta: [sua solução/recomendação]
- Voto: [sua escolha final]
- Justificativa: [por que esta é a melhor opção]

Responda de forma estruturada e técnica.
"""


def _build_followup_prompt(problema: str, contexto: str, historico: List[Dict]) -> str:
    """Constrói prompt das rodadas subsequentes."""
    ultima_rodada = historico[-1]
    rodada_num = len(historico) + 1
    
    prompt = f"""# DEBATE SACI v1.0 - RODADA {rodada_num}

## PROBLEMA ORIGINAL:
{problema}

## RESPOSTAS DA RODADA ANTERIOR:

"""
    
    for model_key, resp_data in ultima_rodada['respostas'].items():
        if resp_data['success']:
            prompt += f"\n{'='*60}\n"
            prompt += f"💬 {resp_data['model_name']}:\n"
            prompt += f"{'='*60}\n"
            prompt += resp_data['response'][:800] + "...\n"
    
    prompt += f"""

## SUA TAREFA:
1. Avalie as propostas dos outros modelos
2. Identifique pontos de consenso e divergência
3. Refine sua proposta ou adote a melhor proposta apresentada
4. Vote claramente na solução final que você apoia

## OBJETIVO:
Convergir para uma solução consensual. Se concordar com outro modelo, DECLARE explicitamente.

Responda de forma estruturada indicando seu voto final.
"""
    
    return prompt


def _extract_votes(respostas: Dict) -> Dict:
    """
    Extrai votos das respostas dos modelos.
    
    Estratégia simples: conta palavras-chave como "PostgreSQL", "MongoDB", etc.
    Para v2.0, usaremos parsing JSON estruturado.
    """
    votos = {}
    
    for model_key, resp_data in respostas.items():
        if not resp_data['success']:
            continue
        
        response_lower = resp_data['response'].lower()
        
        # Extração simples baseada em keywords
        # TODO: melhorar para v2.0 com JSON estruturado
        voto = "unclear"
        
        # Buscar padrões de voto explícito
        if "voto:" in response_lower or "vote:" in response_lower:
            # Extrair após "voto:"
            parts = response_lower.split("voto:")
            if len(parts) > 1:
                voto_section = parts[1][:200]
                # Primeira palavra significativa
                words = voto_section.split()
                if words:
                    voto = words[0].strip('.,;:!?')
        
        votos[model_key] = voto
    
    return votos


def _check_consensus(votos: Dict, threshold: float, respostas: Dict) -> tuple:
    """
    Verifica se houve consenso.
    
    Returns:
        (consenso_atingido: bool, solucao_final: str)
    """
    if not votos:
        return False, None
    
    # Contar votos
    contagem = {}
    for voto in votos.values():
        contagem[voto] = contagem.get(voto, 0) + 1
    
    total_votos = len(votos)
    voto_majoritario = max(contagem, key=contagem.get)
    qtd_majoritaria = contagem[voto_majoritario]
    
    percentual = qtd_majoritaria / total_votos
    
    if percentual >= threshold:
        # Consenso atingido - sintetizar solução
        solucao = f"Consenso: {voto_majoritario} ({qtd_majoritaria}/{total_votos} votos = {percentual*100:.0f}%)"
        
        # Adicionar justificativas dos modelos que votaram pela opção vencedora
        for model_key, voto in votos.items():
            if voto == voto_majoritario and respostas[model_key]['success']:
                resp = respostas[model_key]['response'][:500]
                solucao += f"\n\n{respostas[model_key]['model_name']}: {resp}..."
        
        return True, solucao
    
    return False, None


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def verificar_saci_disponivel() -> Dict[str, bool]:
    """
    Verifica se todos os modelos da SACI estão disponíveis.
    
    Returns:
        Dict com status de cada modelo
    """
    status = {}
    
    for model_key, model_info in SACI_MODELS.items():
        try:
            # Teste rápido com prompt mínimo
            response = chat(
                model=model_info['id'],
                system="Test",
                user="Respond with 'OK'",
                max_tokens=10,
                temperature=0
            )
            status[model_key] = True
        except Exception as e:
            status[model_key] = False
            print(f"❌ {model_info['name']}: {e}")
    
    return status


def get_saci_info() -> Dict:
    """Retorna informações sobre a SACI v1.0."""
    return {
        'versao': '1.0',
        'modelos': SACI_MODELS,
        'threshold_consenso': 0.75,
        'descricao': 'Sistema Avançado de Convergência de Ideias - Versão estável',
        'proxima_versao': '2.0 (SACI EVOLUÍDA - em desenvolvimento)',
        'quando_migrar': 'Apenas quando v2.0 demonstrar superioridade comprovada'
    }


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Exemplo simples
    resultado = debate_saci(
        problema="Qual banco de dados é mais adequado para um e-commerce: PostgreSQL ou MongoDB?",
        contexto="Sistema com alta consistência transacional, volume médio (100k pedidos/dia), equipe pequena.",
        max_rodadas=2
    )
    
    print("\n" + "="*80)
    print("RESULTADO FINAL")
    print("="*80)
    print(f"\nConsenso: {resultado['consenso']}")
    if resultado['consenso']:
        print(f"\nSolução:\n{resultado['solucao_final']}")
    print(f"\nRodadas executadas: {len(resultado['rodadas'])}")
