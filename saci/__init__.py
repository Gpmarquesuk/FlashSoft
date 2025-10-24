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
]
