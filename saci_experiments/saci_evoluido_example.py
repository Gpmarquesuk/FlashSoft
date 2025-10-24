#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SACI EVOLUÍDO - Exemplo de Integração
======================================
Demonstra como usar os módulos do SACI EVOLUÍDO com código existente.

Este exemplo mostra:
1. Integração com debate multi-agent existente
2. Early stopping automático
3. Logging estruturado
4. Export de métricas
"""

import os
import sys
from typing import List, Tuple

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from saci import DynamicDebate, TraceLogger, create_trace_from_round_result
from llm_client import chat


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

AGENTS = [
    {"name": "Claude", "model": "anthropic/claude-sonnet-4.5"},
    {"name": "GPT-5", "model": "openai/gpt-5-codex"},
    {"name": "Gemini", "model": "google/gemini-2.5-pro"},
    {"name": "Grok", "model": "x-ai/grok-4"},
]


# ============================================================================
# FUNÇÃO DE DEBATE (ADAPTER)
# ============================================================================

def simple_debate_function(prompt: str, round_num: int) -> Tuple[List[str], List[str]]:
    """
    Função de debate que pode ser injetada no DynamicDebate.
    
    Esta é a "cola" entre o código existente e o SACI EVOLUÍDO.
    Adapta a assinatura esperada pelo round_manager.
    
    Args:
        prompt: Questão do debate
        round_num: Número da rodada atual
        
    Returns:
        Tupla (responses, agents) onde:
        - responses: Lista de respostas textuais
        - agents: Lista de nomes dos agentes
    """
    print(f"\n--- RODADA {round_num} ---")
    
    # Adaptar prompt baseado na rodada
    if round_num == 1:
        system_msg = "You are an expert technical advisor. Analyze the question and vote for the best option. Format your response as: VOTE: [option_name]. Then explain your reasoning."
        user_prompt = prompt
    elif round_num == 2:
        system_msg = "You are a critical reviewer. Challenge the previous consensus and identify potential issues."
        user_prompt = f"Previous debate: {prompt}\n\nWhat are the risks and counterarguments?"
    else:
        system_msg = "You are building final consensus. Review all arguments and vote for the final decision."
        user_prompt = f"After discussion: {prompt}\n\nWhat is your FINAL VOTE?"
    
    responses = []
    agent_names = []
    
    for agent in AGENTS:
        try:
            response = chat(
                model=agent["model"],
                system=system_msg,
                user=user_prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            responses.append(response)
            agent_names.append(agent["name"])
            print(f"  ✓ {agent['name']}: {response[:80]}...")
            
        except Exception as e:
            print(f"  ✗ {agent['name']}: ERROR - {e}")
            # Continuar com outros agentes mesmo se um falhar
    
    return responses, agent_names


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

def main():
    """Exemplo completo de uso do SACI EVOLUÍDO"""
    
    print("=" * 80)
    print("SACI EVOLUÍDO - Exemplo de Integração")
    print("=" * 80)
    
    # Verificar API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ ERRO: OPENROUTER_API_KEY não configurada!")
        sys.exit(1)
    
    # Questão do debate
    question = """
    Para uma startup de fintech processando 100K transações/dia,
    qual banco de dados escolher?
    
    Opções:
    - PostgreSQL (SQL tradicional, ACID)
    - MongoDB (NoSQL, escalabilidade)
    - CockroachDB (SQL distribuído)
    
    Vote na melhor opção e justifique.
    """
    
    # Criar logger
    logger = TraceLogger(debate_id="fintech_db_decision")
    
    # Criar orquestrador com early stopping
    debate = DynamicDebate(
        debate_fn=simple_debate_function,
        threshold=0.75,  # Para se 75% de convergência
        min_rounds=3,    # Mínimo 3 rodadas
        max_rounds=5,    # Máximo 5 rodadas
        semantic_weight=0.6,
        vote_weight=0.4
    )
    
    print(f"\nQuestão: {question.strip()}")
    print(f"\nConfiguração:")
    print(f"  - Threshold: {debate.threshold}")
    print(f"  - Min rounds: {debate.min_rounds}")
    print(f"  - Max rounds: {debate.max_rounds}")
    print(f"  - Weights: {debate.semantic_weight:.1f} semantic + {debate.vote_weight:.1f} votes")
    
    # Executar debate
    print("\n" + "=" * 80)
    print("EXECUTANDO DEBATE COM EARLY STOPPING")
    print("=" * 80)
    
    try:
        results = debate.run(question)
        
        # Logar cada rodada
        for result in results:
            trace = create_trace_from_round_result(result)
            logger.log_round(
                round_num=result.round_num,
                agents=result.agents,
                responses=result.responses,
                convergence_score=result.convergence_score,
                metadata=result.metadata
            )
        
        # Resultado final
        consensus = debate.get_final_consensus(results)
        
        print("\n" + "=" * 80)
        print("RESULTADO FINAL")
        print("=" * 80)
        print(f"\n{logger.summary()}")
        
        print(f"\nConsensual decision: {logger.get_majority_vote()}")
        print(f"Converged: {'✓ YES' if consensus['converged'] else '✗ NO'}")
        print(f"Stopped early: {'✓ YES' if consensus['stopped_early'] else '✗ NO'}")
        print(f"Total rounds: {consensus['total_rounds']}/{debate.max_rounds}")
        
        # Export JSON
        json_path = "logs/saci_evoluido_example.json"
        logger.export_json(json_path)
        
        print(f"\n📊 Trajetória de convergência: {logger.get_convergence_trajectory()}")
        print(f"📊 Votos finais: {logger.get_final_votes()}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Debate interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERRO: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
