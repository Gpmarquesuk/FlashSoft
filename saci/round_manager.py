#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SACI EVOLUÍDO - Round Manager (Fase 2)
=======================================
Orquestração de rodadas dinâmicas com early stopping.

Features:
- Rodadas adaptativas (mín 3, máx 5)
- Early stopping baseado em threshold de convergência
- Integração com métricas via adapter pattern

Filosofia: Dependency injection, zero acoplamento com código atual.
"""

from typing import Callable, List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

from .convergence_metrics import calculate_convergence_score


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class RoundResult:
    """Resultado de uma rodada individual do debate"""
    round_num: int
    responses: List[str]  # Respostas textuais dos agentes
    agents: List[str]  # Nomes dos agentes
    convergence_score: float
    metadata: Dict[str, Any]  # Metadados das métricas


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def should_stop_early(
    score: float,
    round_num: int,
    threshold: float = 0.75,
    min_rounds: int = 3
) -> bool:
    """
    Decide se deve parar as rodadas antecipadamente.
    
    Lógica:
    1. Sempre completa mínimo de rodadas (padrão: 3)
    2. Após mínimo, para se score >= threshold
    
    Args:
        score: Score de convergência atual (0-1)
        round_num: Número da rodada atual (1-indexed)
        threshold: Limiar de convergência (padrão: 0.75)
        min_rounds: Mínimo de rodadas obrigatórias (padrão: 3)
        
    Returns:
        True se deve parar, False se deve continuar
        
    Exemplo:
        >>> should_stop_early(0.80, round_num=3, threshold=0.75)
        True  # Passou do mínimo E atingiu threshold
        
        >>> should_stop_early(0.80, round_num=2, threshold=0.75)
        False  # Ainda não completou mínimo
        
        >>> should_stop_early(0.60, round_num=4, threshold=0.75)
        False  # Não atingiu threshold
    """
    # Regra 1: Nunca para antes do mínimo
    if round_num < min_rounds:
        return False
    
    # Regra 2: Após mínimo, para se atingiu threshold
    return score >= threshold


# ============================================================================
# CLASSE PRINCIPAL
# ============================================================================

class DynamicDebate:
    """
    Orquestrador de debates multi-agent com early stopping.
    
    Usa dependency injection para integrar com qualquer função de debate,
    sem modificar código existente (adapter pattern).
    
    Exemplo de uso:
        >>> def my_debate_fn(prompt, round_num):
        ...     # Executa rodada de debate
        ...     return ["response1", "response2", "response3"]
        
        >>> debate = DynamicDebate(
        ...     debate_fn=my_debate_fn,
        ...     threshold=0.75,
        ...     max_rounds=5
        ... )
        
        >>> results = debate.run(prompt="Qual tech stack usar?")
        >>> print(f"Convergiu em {len(results)} rodadas")
        >>> print(f"Score final: {results[-1].convergence_score}")
    """
    
    def __init__(
        self,
        debate_fn: Callable[[str, int], Tuple[List[str], List[str]]],
        threshold: float = 0.75,
        min_rounds: int = 3,
        max_rounds: int = 5,
        semantic_weight: float = 0.6,
        vote_weight: float = 0.4
    ):
        """
        Inicializa orquestrador de debates dinâmicos.
        
        Args:
            debate_fn: Função que executa uma rodada de debate.
                       Assinatura: (prompt: str, round_num: int) -> (responses, agents)
            threshold: Score mínimo para convergência (0-1)
            min_rounds: Mínimo de rodadas obrigatórias
            max_rounds: Máximo de rodadas permitidas
            semantic_weight: Peso da similaridade semântica no score
            vote_weight: Peso do consenso de votos no score
        """
        self.debate_fn = debate_fn
        self.threshold = threshold
        self.min_rounds = min_rounds
        self.max_rounds = max_rounds
        self.semantic_weight = semantic_weight
        self.vote_weight = vote_weight
    
    def run(self, prompt: str) -> List[RoundResult]:
        """
        Executa debate com rodadas dinâmicas e early stopping.
        
        Args:
            prompt: Questão/prompt inicial do debate
            
        Returns:
            Lista de RoundResult, uma para cada rodada executada
            
        Raises:
            ValueError: Se debate_fn retornar formato inválido
        """
        results: List[RoundResult] = []
        
        for round_num in range(1, self.max_rounds + 1):
            # Executar rodada via função injetada
            try:
                responses, agents = self.debate_fn(prompt, round_num)
            except Exception as e:
                print(f"[ERROR] Debate function failed at round {round_num}: {e}")
                break
            
            # Validar retorno
            if not isinstance(responses, list) or not isinstance(agents, list):
                raise ValueError(
                    f"debate_fn must return (List[str], List[str]), "
                    f"got ({type(responses)}, {type(agents)})"
                )
            
            if len(responses) != len(agents):
                raise ValueError(
                    f"Mismatch: {len(responses)} responses but {len(agents)} agents"
                )
            
            # Calcular convergência
            score, metadata = calculate_convergence_score(
                responses,
                semantic_weight=self.semantic_weight,
                vote_weight=self.vote_weight
            )
            
            # Criar resultado
            result = RoundResult(
                round_num=round_num,
                responses=responses,
                agents=agents,
                convergence_score=score,
                metadata=metadata
            )
            
            results.append(result)
            
            # Logging
            print(f"  Rodada {round_num}: Score {score:.3f} | "
                  f"Semantic {metadata['semantic_similarity']:.3f} | "
                  f"Votes {metadata['vote_consensus']:.3f}")
            
            # Early stopping?
            if should_stop_early(score, round_num, self.threshold, self.min_rounds):
                print(f"  ✓ Convergência atingida! (score {score:.3f} >= {self.threshold})")
                break
            
            # Se chegou no máximo sem convergir
            if round_num == self.max_rounds:
                print(f"  ⚠ Máximo de rodadas atingido sem convergência total "
                      f"(score {score:.3f} < {self.threshold})")
        
        return results
    
    def get_final_consensus(self, results: List[RoundResult]) -> Dict[str, Any]:
        """
        Extrai consenso final dos resultados das rodadas.
        
        Args:
            results: Lista de RoundResult do debate
            
        Returns:
            Dict com consenso final, incluindo:
            - converged: bool (se atingiu threshold)
            - final_score: float
            - total_rounds: int
            - votes: dict com contagem de votos
            - responses: list das respostas finais
        """
        if not results:
            return {
                "converged": False,
                "final_score": 0.0,
                "total_rounds": 0,
                "error": "No results"
            }
        
        last_result = results[-1]
        
        return {
            "converged": last_result.convergence_score >= self.threshold,
            "final_score": last_result.convergence_score,
            "total_rounds": len(results),
            "votes": last_result.metadata.get('votes', {}),
            "semantic_similarity": last_result.metadata.get('semantic_similarity', 0.0),
            "vote_consensus": last_result.metadata.get('vote_consensus', 0.0),
            "responses": last_result.responses,
            "agents": last_result.agents,
            "stopped_early": len(results) < self.max_rounds,
            "threshold": self.threshold
        }


# ============================================================================
# FUNÇÕES HELPER (SEM ESTADO)
# ============================================================================

def run_dynamic_rounds(
    debate_fn: Callable,
    prompt: str,
    threshold: float = 0.75,
    min_rounds: int = 3,
    max_rounds: int = 5
) -> List[RoundResult]:
    """
    Função helper para executar debates dinâmicos sem instanciar classe.
    
    Útil para uso rápido/scripts one-off.
    
    Args:
        debate_fn: Função de debate (prompt, round_num) -> (responses, agents)
        prompt: Prompt inicial
        threshold: Threshold de convergência
        min_rounds: Mínimo de rodadas
        max_rounds: Máximo de rodadas
        
    Returns:
        Lista de RoundResult
        
    Exemplo:
        >>> results = run_dynamic_rounds(
        ...     debate_fn=my_debate,
        ...     prompt="SQL ou NoSQL?",
        ...     threshold=0.80
        ... )
    """
    debate = DynamicDebate(
        debate_fn=debate_fn,
        threshold=threshold,
        min_rounds=min_rounds,
        max_rounds=max_rounds
    )
    
    return debate.run(prompt)
