#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SACI EVOLUÍDO - Convergence Metrics (Fase 1)
=============================================
Funções puras para calcular métricas de convergência objetivas.

Features:
- Similaridade semântica via embeddings OpenAI
- Extração de votos estruturados (parsing JSON/regex)
- Score de convergência híbrido (0.6 * similaridade + 0.4 * votos)

Filosofia: Funções puras, zero state, testabilidade máxima.

CORREÇÕES v2.0.1 (Consenso SACI 4/4 modelos):
- ✅ Logging adequado (não fallback silencioso)
- ✅ Exceções não suprimidas
- ✅ Erros reportados claramente
"""

import os
import json
import re
import logging
from typing import List, Dict, Optional, Tuple
from openai import OpenAI

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CACHE SIMPLES (LRU-like) PARA EMBEDDINGS
# ============================================================================

_embedding_cache: Dict[str, List[float]] = {}
MAX_CACHE_SIZE = 100


def _get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Obtém embedding do texto via OpenAI (com cache simples).
    
    Args:
        text: Texto para gerar embedding
        model: Modelo de embedding OpenAI
        
    Returns:
        Lista de floats representando o embedding
        
    Raises:
        Exception: Se API falhar (não faz fallback silencioso)
    """
    # Cache hit
    cache_key = f"{model}:{text[:100]}"  # Usa primeiros 100 chars como key
    if cache_key in _embedding_cache:
        logger.debug(f"Cache HIT para embedding: {text[:50]}...")
        return _embedding_cache[cache_key]
    
    # Cache miss - chamar API
    logger.info(f"Gerando embedding via API: {text[:50]}...")
    
    try:
        client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            timeout=30.0,  # Aumentado de 10s para 30s (consenso)
            max_retries=2   # Retry logic (consenso)
        )
        
        response = client.embeddings.create(
            model=model,
            input=text[:8000]  # Limita tamanho
        )
        
        embedding = response.data[0].embedding
        logger.info(f"✅ Embedding gerado com sucesso: {len(embedding)} dimensões")
        
        # Adicionar ao cache (FIFO se cheio)
        if len(_embedding_cache) >= MAX_CACHE_SIZE:
            # Remove primeiro item (mais antigo)
            first_key = next(iter(_embedding_cache))
            del _embedding_cache[first_key]
        
        _embedding_cache[cache_key] = embedding
        return embedding
        
    except Exception as e:
        # NÃO fazer fallback silencioso (consenso 4/4 modelos)
        logger.critical(f"❌ EMBEDDINGS API FAILURE: {type(e).__name__}: {e}")
        logger.critical(f"   Texto: {text[:100]}...")
        logger.critical(f"   API Key configurada: {bool(os.getenv('OPENROUTER_API_KEY'))}")
        raise  # Propaga exceção ao invés de retornar 0.0


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calcula similaridade de cosseno entre dois vetores.
    
    Args:
        vec1, vec2: Vetores de floats
        
    Returns:
        Float entre -1 (opostos) e 1 (idênticos), normalmente 0-1
    """
    import math
    
    # Produto escalar
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Magnitudes
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    
    # Evitar divisão por zero
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    return dot_product / (mag1 * mag2)


# ============================================================================
# MÉTRICAS PÚBLICAS
# ============================================================================

def compute_semantic_similarity(texts: List[str]) -> float:
    """
    Calcula similaridade semântica média entre todos os pares de textos.
    
    Esta métrica detecta quando agentes convergem em conteúdo semântico,
    mesmo usando palavras diferentes (ex: "deploy agora" vs "lançar imediatamente").
    
    Args:
        texts: Lista de respostas textuais dos agentes
        
    Returns:
        Float entre 0 (divergência total) e 1 (consenso perfeito)
        
    Raises:
        Exception: Se embeddings falharem (não retorna 0.0 silenciosamente)
        
    Exemplo:
        >>> texts = ["Use SQL", "Use SQL", "Use SQL"]
        >>> compute_semantic_similarity(texts)
        0.98  # Alta similaridade
        
        >>> texts = ["Use SQL", "Use NoSQL", "Use GraphDB"]
        >>> compute_semantic_similarity(texts)
        0.32  # Baixa similaridade
    """
    if len(texts) < 2:
        return 1.0  # Single text = convergência perfeita
    
    logger.info(f"Calculando similaridade semântica para {len(texts)} textos...")
    
    try:
        # Gerar embeddings para todos os textos
        embeddings = [_get_embedding(text) for text in texts]
        logger.info(f"✅ {len(embeddings)} embeddings gerados com sucesso")
        
        # Calcular similaridade para todos os pares
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = _cosine_similarity(embeddings[i], embeddings[j])
                similarities.append(sim)
        
        # Retornar média
        if not similarities:
            return 0.5  # Fallback neutro
        
        avg_similarity = sum(similarities) / len(similarities)
        logger.info(f"📊 Similaridade média: {avg_similarity:.3f}")
        
        # Normalizar para 0-1 (cosseno pode ser negativo, embora raro)
        result = max(0.0, min(1.0, avg_similarity))
        return result
        
    except Exception as e:
        # NÃO fazer fallback silencioso (consenso 4/4)
        logger.critical(f"❌ compute_semantic_similarity FAILED: {e}")
        raise  # Propaga exceção


def extract_structured_votes(responses: List[str]) -> Dict[str, int]:
    """
    Extrai votos estruturados das respostas dos agentes.
    
    Procura por padrões como:
    - JSON: {"vote": "option_a", ...}
    - Texto: [VOTE: option_a]
    - Texto: DECISÃO: option_a
    
    Args:
        responses: Lista de respostas textuais
        
    Returns:
        Dict mapeando opções -> contagem de votos
        Ex: {"option_a": 3, "option_b": 1}
        
    Exemplo:
        >>> responses = [
        ...     '{"vote": "microservices"}',
        ...     'Eu voto em microservices',
        ...     '[VOTE: microservices]',
        ...     'monolito é melhor'
        ... ]
        >>> extract_structured_votes(responses)
        {"microservices": 3, "monolito": 1}
    """
    votes: Dict[str, int] = {}
    
    for response in responses:
        vote_option = None
        
        # Estratégia 1: Tentar parsear JSON
        try:
            data = json.loads(response)
            if isinstance(data, dict):
                # Procurar chaves comuns de voto
                for key in ['vote', 'decision', 'choice', 'option', 'recommendation']:
                    if key in data:
                        vote_option = str(data[key]).lower()
                        break
        except:
            pass
        
        # Estratégia 2: Regex para padrões de voto
        if not vote_option:
            patterns = [
                r'\[VOTE:\s*(\w+)\]',
                r'\bvote[:\s]+(\w+)',
                r'\bdecis[aã]o[:\s]+(\w+)',
                r'\bescolh[ao][:\s]+(\w+)',
                r'\bopç[aã]o[:\s]+(\w+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    vote_option = match.group(1).lower()
                    break
        
        # Estratégia 3: Fallback - detectar palavras-chave comuns em decisões técnicas
        if not vote_option:
            keywords = [
                'sql', 'nosql', 'graphdb', 'mongodb', 'postgres',
                'microservices', 'microserviços', 'monolito', 'monolith',
                'cloud', 'on-premise', 'kubernetes', 'docker',
                'react', 'vue', 'angular', 'python', 'javascript'
            ]
            
            response_lower = response.lower()
            for keyword in keywords:
                if keyword in response_lower:
                    # Verificar se não está negando (heurística simples)
                    if not re.search(rf'n[aã]o\s+{keyword}|not\s+{keyword}', response_lower):
                        vote_option = keyword
                        break
        
        # Registrar voto (ou "unclear" se não conseguiu detectar)
        if vote_option:
            votes[vote_option] = votes.get(vote_option, 0) + 1
        else:
            votes['unclear'] = votes.get('unclear', 0) + 1
    
    return votes


def calculate_convergence_score(
    texts: List[str],
    semantic_weight: float = 0.6,
    vote_weight: float = 0.4
) -> Tuple[float, Dict]:
    """
    Calcula score final de convergência combinando similaridade + votos.
    
    Fórmula:
        score = (semantic_weight * similarity) + (vote_weight * vote_consensus)
    
    Onde:
        - similarity: avg similaridade semântica (0-1)
        - vote_consensus: proporção do voto majoritário (0-1)
    
    Args:
        texts: Lista de respostas dos agentes
        semantic_weight: Peso da similaridade semântica (padrão 0.6)
        vote_weight: Peso do consenso de votos (padrão 0.4)
        
    Returns:
        Tupla (score, metadata) onde:
        - score: Float 0-1 indicando nível de convergência
        - metadata: Dict com detalhes (similarity, votes, etc.)
        
    Exemplo:
        >>> texts = ["Use SQL", "Use SQL", "Use SQL", "Use NoSQL"]
        >>> score, meta = calculate_convergence_score(texts)
        >>> score
        0.78  # Alta convergência (3/4 SQL + alta similaridade)
        >>> meta['votes']
        {"sql": 3, "nosql": 1}
    """
    if not texts:
        return 0.0, {"error": "no texts provided"}
    
    # Calcular componentes
    similarity = compute_semantic_similarity(texts)
    votes = extract_structured_votes(texts)
    
    # Calcular consenso de votos (proporção do voto majoritário)
    vote_consensus = 0.0
    if votes and sum(votes.values()) > 0:
        max_votes = max(votes.values())
        total_votes = sum(votes.values())
        vote_consensus = max_votes / total_votes
    else:
        # Se não conseguiu extrair votos, penaliza score
        vote_consensus = 0.3  # Valor baixo mas não zero
    
    # Score final (weighted average)
    final_score = (semantic_weight * similarity) + (vote_weight * vote_consensus)
    
    # Metadados para debugging/logging
    metadata = {
        "semantic_similarity": round(similarity, 3),
        "vote_consensus": round(vote_consensus, 3),
        "votes": votes,
        "total_agents": len(texts),
        "weights": {
            "semantic": semantic_weight,
            "vote": vote_weight
        },
        "final_score": round(final_score, 3)
    }
    
    return final_score, metadata


# ============================================================================
# FALLBACK: SIMILARIDADE LÉXICA (JACCARD)
# ============================================================================

def compute_jaccard_similarity(texts: List[str]) -> float:
    """
    Fallback: Similaridade de Jaccard (léxica) se embeddings falharem.
    
    Usa interseção de palavras únicas entre textos.
    Menos preciso que embeddings, mas rápido e sem API calls.
    
    Args:
        texts: Lista de textos
        
    Returns:
        Float 0-1 indicando overlap léxico
    """
    if len(texts) < 2:
        return 1.0
    
    # Tokenizar (simples: lowercase + split)
    token_sets = [
        set(text.lower().split())
        for text in texts
    ]
    
    # Calcular Jaccard para todos os pares
    similarities = []
    for i in range(len(token_sets)):
        for j in range(i + 1, len(token_sets)):
            intersection = len(token_sets[i] & token_sets[j])
            union = len(token_sets[i] | token_sets[j])
            
            if union == 0:
                sim = 0.0
            else:
                sim = intersection / union
            
            similarities.append(sim)
    
    if not similarities:
        return 0.5
    
    return sum(similarities) / len(similarities)
