"""
SACI EVOLUÍDO - Sistema de Análise de Consenso por IA
=======================================================
Implementação consensual (Fases 1+2) sem LangGraph/AutoGen.

Módulos:
- convergence_metrics: Métricas quantitativas (similaridade + votos)
- round_manager: Orquestração de rodadas dinâmicas com early stopping
- trace_logger: Rastreabilidade estruturada em JSON

Filosofia:
- Simplicidade radical (pure functions, zero heavy dependencies)
- Auditabilidade nativa (scores 0-1, JSON estruturado)
- Adaptabilidade (early stopping baseado em threshold)
"""

__version__ = "0.1.0"
__author__ = "FlashSoft Team (via SACI Consensus)"

from .convergence_metrics import (
    compute_semantic_similarity,
    extract_structured_votes,
    calculate_convergence_score
)

from .round_manager import (
    DynamicDebate,
    should_stop_early
)

from .trace_logger import (
    TraceLogger,
    RoundTrace,
    create_trace_from_round_result
)

# Função helper de alto nível
def run_saci_debate(
    debate_id: str,
    question: str,
    agents: list,
    threshold: float = 0.75,
    min_rounds: int = 3,
    max_rounds: int = 5,
    weights: tuple = (0.6, 0.4)
):
    """
    Executa um debate SACI completo com early stopping.
    
    Args:
        debate_id: Identificador único do debate
        question: Pergunta/questão a ser debatida
        agents: Lista de dicts com {name, model, max_tokens}
        threshold: Score mínimo para convergência (0-1)
        min_rounds: Mínimo de rodadas obrigatórias
        max_rounds: Máximo de rodadas permitidas
        weights: (peso_semantic, peso_votes) padrão (0.6, 0.4)
    
    Returns:
        dict com resultado final, tracer, scores, etc.
    """
    from llm_client import chat
    import time
    
    tracer = TraceLogger()
    all_responses = []
    score_trajectory = []
    converged = False
    
    for round_num in range(1, max_rounds + 1):
        print(f"\n--- RODADA {round_num} ---")
        responses = []
        
        # Coletar respostas dos agentes
        for agent in agents:
            try:
                response = chat(
                    model=agent["model"],
                    system=f"You are {agent['name']}. Participate in a technical debate. Vote clearly (VOTE: option) and justify.",
                    user=f"# ROUND {round_num}\n\n{question}",
                    temperature=0.3,
                    max_tokens=agent.get("max_tokens", 4096)
                )
                responses.append(response)
                print(f"  ✓ {agent['name'][:20]}: {response[:80]}...")
            except Exception as e:
                print(f"  ✗ {agent['name']}: ERROR - {str(e)[:50]}")
                responses.append(f"[ERROR: {str(e)}]")
            
            time.sleep(2)  # Rate limiting
        
        all_responses.extend(responses)
        
        # Calcular métricas (função calcula tudo internamente)
        score, metadata = calculate_convergence_score(responses, weights[0], weights[1])
        similarity = metadata.get('similarity', 0.0)
        votes = metadata.get('votes', {})
        
        score_trajectory.append(score)
        
        # Log da rodada
        agent_names = [agent['name'] for agent in agents]
        tracer.log_round(
            round_num=round_num,
            agents=agent_names,
            responses=responses,
            convergence_score=score,
            metadata=metadata
        )
        
        # Determinar voto majoritário
        if votes:
            majority = max(votes.items(), key=lambda x: x[1])
            print(f"  Rodada {round_num}: Score {score:.3f} | Semantic {similarity:.3f} | Votes {votes.get(majority[0], 0)}/{sum(votes.values())}")
        else:
            print(f"  Rodada {round_num}: Score {score:.3f} | Semantic {similarity:.3f} | Votes N/A")
        
        # Early stopping
        if should_stop_early(score, round_num, threshold, min_rounds):
            converged = True
            print(f"  ✓ Convergência atingida! (score {score:.3f} >= {threshold})")
            break
    
    # Resultado final
    if not converged:
        if round_num >= max_rounds:
            print(f"  ⚠ Máximo de rodadas atingido sem convergência total (score {score:.3f} < {threshold})")
        else:
            print(f"  ✓ Convergência atingida na rodada {round_num}")
    
    # Determinar decisão consensual
    consensual_decision = None
    if votes:
        majority_option = max(votes.items(), key=lambda x: x[1])
        if majority_option[1] >= len(agents) * 0.75:  # 75% dos agentes
            consensual_decision = majority_option[0]
    
    return {
        "debate_id": debate_id,
        "total_rounds": round_num,
        "final_score": score,
        "converged": converged,
        "consensual_decision": consensual_decision,
        "score_trajectory": score_trajectory,
        "final_votes": votes,
        "tracer": tracer,
        "all_responses": all_responses
    }


__all__ = [
    # Métricas
    'compute_semantic_similarity',
    'extract_structured_votes',
    'calculate_convergence_score',
    
    # Orquestração
    'DynamicDebate',
    'should_stop_early',
    
    # Observabilidade
    'TraceLogger',
    'RoundTrace',
    'create_trace_from_round_result',
    
    # Helper
    'run_saci_debate',
]
