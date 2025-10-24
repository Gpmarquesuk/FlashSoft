#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SACI EVOLUÍDO - Trace Logger (Fase 3)
======================================
Rastreabilidade estruturada em JSON para auditoria e compliance.

Features:
- Logs estruturados por rodada (scores + textos + timestamps)
- Export para JSON (humano-legível + machine-parseable)
- Suporte a metadados customizados

Filosofia: Estado mínimo, interface simples, zero dependencies extras.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class RoundTrace:
    """
    Trace de uma rodada individual do debate.
    
    Captura todas as informações relevantes para auditoria:
    - Inputs (respostas dos agentes)
    - Outputs (métricas de convergência)
    - Metadados (timestamp, configuração)
    """
    round_num: int
    timestamp: str
    agents: List[str]
    responses: List[str]
    convergence_score: float
    semantic_similarity: float
    vote_consensus: float
    votes: Dict[str, int]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dict JSON-serializável"""
        return asdict(self)
    
    def summary(self) -> str:
        """Retorna resumo textual da rodada (para logging/prints)"""
        majority_vote = max(self.votes.items(), key=lambda x: x[1])[0] if self.votes else "unclear"
        
        return (
            f"Round {self.round_num}: "
            f"Score={self.convergence_score:.3f} "
            f"(Semantic={self.semantic_similarity:.3f}, "
            f"Votes={self.vote_consensus:.3f}) | "
            f"Majority: {majority_vote} ({self.votes.get(majority_vote, 0)}/{len(self.agents)})"
        )


# ============================================================================
# LOGGER
# ============================================================================

class TraceLogger:
    """
    Logger de traces estruturados para debates SACI.
    
    Mantém histórico em memória e permite export para JSON.
    Design: Estado mínimo, append-only (não modifica traces passados).
    
    Exemplo de uso:
        >>> logger = TraceLogger(debate_id="tech_stack_decision")
        
        >>> # Após cada rodada
        >>> logger.log_round(
        ...     round_num=1,
        ...     agents=["Claude", "GPT", "Gemini"],
        ...     responses=["Use SQL", "Use SQL", "Use NoSQL"],
        ...     convergence_score=0.68,
        ...     metadata={"semantic_similarity": 0.72, ...}
        ... )
        
        >>> # No final
        >>> logger.export_json("debate_log.json")
        >>> print(logger.summary())
    """
    
    def __init__(self, debate_id: Optional[str] = None):
        """
        Inicializa logger.
        
        Args:
            debate_id: Identificador único do debate (opcional, auto-gerado se omitido)
        """
        self.debate_id = debate_id or f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.traces: List[RoundTrace] = []
        self.started_at = datetime.now().isoformat()
    
    def log_round(
        self,
        round_num: int,
        agents: List[str],
        responses: List[str],
        convergence_score: float,
        metadata: Dict[str, Any]
    ) -> RoundTrace:
        """
        Registra uma rodada do debate.
        
        Args:
            round_num: Número da rodada (1-indexed)
            agents: Lista de nomes dos agentes
            responses: Lista de respostas textuais
            convergence_score: Score de convergência final (0-1)
            metadata: Dict com métricas detalhadas (semantic_similarity, votes, etc.)
            
        Returns:
            RoundTrace criado e adicionado ao histórico
        """
        trace = RoundTrace(
            round_num=round_num,
            timestamp=datetime.now().isoformat(),
            agents=agents,
            responses=responses,
            convergence_score=convergence_score,
            semantic_similarity=metadata.get('semantic_similarity', 0.0),
            vote_consensus=metadata.get('vote_consensus', 0.0),
            votes=metadata.get('votes', {}),
            metadata=metadata
        )
        
        self.traces.append(trace)
        return trace
    
    def export_json(self, filepath: Optional[str] = None) -> str:
        """
        Exporta traces para JSON.
        
        Args:
            filepath: Caminho do arquivo (opcional). Se omitido, retorna string JSON.
            
        Returns:
            String JSON dos traces
            
        Raises:
            IOError: Se falhar ao escrever arquivo
        """
        output = {
            "debate_id": self.debate_id,
            "started_at": self.started_at,
            "finished_at": datetime.now().isoformat(),
            "total_rounds": len(self.traces),
            "final_score": self.traces[-1].convergence_score if self.traces else 0.0,
            "converged": self.traces[-1].convergence_score >= 0.75 if self.traces else False,
            "traces": [trace.to_dict() for trace in self.traces]
        }
        
        json_str = json.dumps(output, indent=2, ensure_ascii=False)
        
        # Salvar em arquivo se filepath fornecido
        if filepath:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
            print(f"  💾 Trace log exportado: {filepath}")
        
        return json_str
    
    def summary(self) -> str:
        """
        Retorna resumo textual do debate completo.
        
        Returns:
            String multi-linha com sumário executivo
        """
        if not self.traces:
            return f"Debate '{self.debate_id}': Nenhuma rodada registrada"
        
        lines = [
            f"Debate ID: {self.debate_id}",
            f"Rodadas: {len(self.traces)}",
            f"Score final: {self.traces[-1].convergence_score:.3f}",
            f"Convergiu: {'✓ Sim' if self.traces[-1].convergence_score >= 0.75 else '✗ Não'}",
            "",
            "Evolução por rodada:"
        ]
        
        for trace in self.traces:
            lines.append(f"  {trace.summary()}")
        
        return "\n".join(lines)
    
    def get_convergence_trajectory(self) -> List[float]:
        """
        Retorna trajetória de scores de convergência ao longo das rodadas.
        
        Útil para plotar gráficos de evolução.
        
        Returns:
            Lista de scores (um por rodada)
        """
        return [trace.convergence_score for trace in self.traces]
    
    def get_final_votes(self) -> Dict[str, int]:
        """
        Retorna votos da última rodada.
        
        Returns:
            Dict com contagem de votos
        """
        if not self.traces:
            return {}
        return self.traces[-1].votes
    
    def get_majority_vote(self) -> Optional[str]:
        """
        Retorna opção com maior número de votos na última rodada.
        
        Returns:
            String com a opção vencedora, ou None se empate/sem votos
        """
        votes = self.get_final_votes()
        if not votes:
            return None
        
        max_votes = max(votes.values())
        winners = [option for option, count in votes.items() if count == max_votes]
        
        # Se empate, retorna None
        if len(winners) > 1:
            return None
        
        return winners[0]


# ============================================================================
# FUNÇÕES HELPER (SEM ESTADO)
# ============================================================================

def create_trace_from_round_result(round_result: Any) -> RoundTrace:
    """
    Converte RoundResult (do round_manager) para RoundTrace.
    
    Facilita integração entre módulos.
    
    Args:
        round_result: Instância de RoundResult
        
    Returns:
        RoundTrace equivalente
    """
    return RoundTrace(
        round_num=round_result.round_num,
        timestamp=datetime.now().isoformat(),
        agents=round_result.agents,
        responses=round_result.responses,
        convergence_score=round_result.convergence_score,
        semantic_similarity=round_result.metadata.get('semantic_similarity', 0.0),
        vote_consensus=round_result.metadata.get('vote_consensus', 0.0),
        votes=round_result.metadata.get('votes', {}),
        metadata=round_result.metadata
    )
