#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTES UNITÁRIOS - SACI v2.0 Convergence Metrics
==================================================

Testes críticos para garantir que embeddings funcionam corretamente.
Implementado baseado no consenso SACI 4/4 modelos.

CORREÇÕES v2.0.1:
- ✅ Test embeddings não retornam 0.0 sempre
- ✅ Test similaridade > 0.0 para textos reais
- ✅ Test fallback silencioso não mascara erros
"""

import os
import pytest
from saci.convergence_metrics import (
    compute_semantic_similarity,
    extract_structured_votes,
    calculate_convergence_score,
    _get_embedding,
    _cosine_similarity
)


# ============================================================================
# TESTES DE EMBEDDINGS (CRÍTICO - Consenso 4/4)
# ============================================================================

def test_embeddings_not_always_zero():
    """
    CONSENSO 4/4 MODELOS: Embeddings NÃO podem retornar 0.0 sempre.
    
    Teste crítico que detectaria o bug relatado nos logs de produção:
    - 15 rodadas de debates
    - Todas com similarity = 0.000
    
    Se embeddings funcionam, similaridade DEVE ser > 0.0 para textos reais.
    """
    texts = [
        "I prefer PostgreSQL for its ACID compliance",
        "PostgreSQL is my choice due to strong consistency",
        "MongoDB is better for our use case"
    ]
    
    try:
        similarity = compute_semantic_similarity(texts)
    except Exception as e:
        pytest.fail(f"Embeddings API falhou: {e}")
    
    # ASSERT CRÍTICO
    assert similarity > 0.0, (
        f"Similaridade = {similarity} (deve ser > 0.0). "
        f"Embeddings API pode não estar funcionando!"
    )
    
    # Primeiros dois textos são similares, terceiro diferente
    # Similaridade deve ser positiva mas < 1.0
    assert 0.3 < similarity < 0.9, (
        f"Similaridade {similarity} fora do esperado (0.3-0.9). "
        f"Verifique cálculo de embeddings."
    )


def test_embedding_single_text():
    """
    Testa que _get_embedding retorna vetor válido para um único texto.
    """
    text = "This is a test"
    
    try:
        embedding = _get_embedding(text)
    except Exception as e:
        pytest.fail(f"_get_embedding falhou: {e}")
    
    # Embedding deve ser uma lista de floats
    assert isinstance(embedding, list), "Embedding deve ser lista"
    assert len(embedding) > 0, "Embedding não pode ser vazio"
    assert all(isinstance(x, (int, float)) for x in embedding), "Embedding deve conter números"
    
    # Não pode ser vetor de zeros (bug comum)
    assert not all(x == 0.0 for x in embedding), "Embedding é vetor de zeros (API falhou silenciosamente)"


def test_cosine_similarity_identical_vectors():
    """
    Vetores idênticos devem ter similaridade = 1.0
    """
    vec = [1.0, 2.0, 3.0, 4.0]
    sim = _cosine_similarity(vec, vec)
    
    assert abs(sim - 1.0) < 0.001, f"Vetores idênticos devem ter sim=1.0, got {sim}"


def test_cosine_similarity_orthogonal_vectors():
    """
    Vetores ortogonais devem ter similaridade = 0.0
    """
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [0.0, 1.0, 0.0]
    sim = _cosine_similarity(vec1, vec2)
    
    assert abs(sim - 0.0) < 0.001, f"Vetores ortogonais devem ter sim=0.0, got {sim}"


def test_cosine_similarity_opposite_vectors():
    """
    Vetores opostos devem ter similaridade = -1.0
    """
    vec1 = [1.0, 2.0, 3.0]
    vec2 = [-1.0, -2.0, -3.0]
    sim = _cosine_similarity(vec1, vec2)
    
    assert abs(sim - (-1.0)) < 0.001, f"Vetores opostos devem ter sim=-1.0, got {sim}"


# ============================================================================
# TESTES DE VOTOS ESTRUTURADOS
# ============================================================================

def test_extract_votes_json_format():
    """
    Testa extração de votos em formato JSON.
    """
    responses = [
        '{"vote": "option_a", "reasoning": "melhor"}',
        '{"vote": "option_a"}',
        '{"vote": "option_b"}',
        '{"vote": "option_a"}'
    ]
    
    votes = extract_structured_votes(responses)
    
    assert votes["option_a"] == 3, f"Expected 3 votes for option_a, got {votes}"
    assert votes["option_b"] == 1, f"Expected 1 vote for option_b, got {votes}"


def test_extract_votes_text_format():
    """
    Testa extração de votos em texto natural.
    """
    responses = [
        "Eu voto em PostgreSQL",
        "Minha escolha é PostgreSQL",
        "Prefiro MongoDB",
        "VOTO: PostgreSQL"
    ]
    
    votes = extract_structured_votes(responses)
    
    assert "postgresql" in votes, f"Deveria detectar votos em PostgreSQL: {votes}"
    assert votes.get("postgresql", 0) >= 2, f"Deveria ter pelo menos 2 votos PostgreSQL: {votes}"


def test_extract_votes_mixed_formats():
    """
    Testa extração com formatos mistos.
    """
    responses = [
        '{"vote": "microservices"}',
        "Eu voto em microservices",
        "DECISÃO: monolith",
        '[VOTE: microservices]'
    ]
    
    votes = extract_structured_votes(responses)
    
    assert "microservices" in votes, f"Deveria detectar microservices: {votes}"
    assert votes["microservices"] >= 2, f"Deveria ter votos em microservices: {votes}"


# ============================================================================
# TESTES DE SCORE DE CONVERGÊNCIA
# ============================================================================

def test_convergence_score_perfect_consensus():
    """
    Consenso perfeito (similarity=1.0, votes=1.0) deve dar score=1.0
    """
    score = calculate_convergence_score(
        texts=["same", "same", "same", "same"],
        semantic_weight=0.6,
        vote_weight=0.4
    )
    
    # Com consenso perfeito, score deve ser alto (próximo de 1.0)
    assert score > 0.9, f"Consenso perfeito deve dar score > 0.9, got {score}"


def test_convergence_score_weights():
    """
    Testa que pesos afetam o score corretamente.
    """
    texts = ["a", "a", "b", "c"]  # 50% similaridade aproximadamente
    
    # Peso maior em semântica
    score_semantic = calculate_convergence_score(texts, 0.8, 0.2)
    
    # Peso maior em votos
    score_votes = calculate_convergence_score(texts, 0.2, 0.8)
    
    # Scores devem ser diferentes
    assert score_semantic != score_votes, "Pesos diferentes devem produzir scores diferentes"


def test_convergence_score_range():
    """
    Score sempre deve estar entre 0.0 e 1.0
    """
    texts = ["divergent", "texts", "that", "differ"]
    
    score = calculate_convergence_score(texts, 0.6, 0.4)
    
    assert 0.0 <= score <= 1.0, f"Score deve estar em [0,1], got {score}"


# ============================================================================
# TESTES DE EDGE CASES
# ============================================================================

def test_semantic_similarity_single_text():
    """
    Um único texto deve ter similaridade = 1.0 (consenso perfeito consigo mesmo)
    """
    similarity = compute_semantic_similarity(["single text"])
    assert similarity == 1.0, f"Single text deve ter similarity=1.0, got {similarity}"


def test_semantic_similarity_empty_list():
    """
    Lista vazia deve retornar 1.0 (sem divergência)
    """
    similarity = compute_semantic_similarity([])
    assert similarity == 1.0, f"Empty list deve ter similarity=1.0, got {similarity}"


def test_extract_votes_empty_responses():
    """
    Respostas vazias não devem crashar.
    """
    votes = extract_structured_votes([])
    assert isinstance(votes, dict), "Deve retornar dict vazio"
    assert len(votes) == 0, "Deve estar vazio"


def test_extract_votes_no_valid_votes():
    """
    Respostas sem votos válidos devem retornar dict vazio ou com "unclear".
    """
    responses = ["texto sem voto", "outro texto qualquer"]
    votes = extract_structured_votes(responses)
    
    assert isinstance(votes, dict), "Deve retornar dict"


# ============================================================================
# TESTES DE ERRO (Anti-Fallback-Silencioso)
# ============================================================================

def test_embeddings_fail_loudly_without_api_key():
    """
    CONSENSO 4/4: Se API key não está configurada, deve FALHAR ruidosamente.
    
    NÃO deve retornar 0.0 silenciosamente.
    """
    # Salvar API key original
    original_key = os.getenv("OPENROUTER_API_KEY")
    
    try:
        # Remover API key temporariamente
        if "OPENROUTER_API_KEY" in os.environ:
            del os.environ["OPENROUTER_API_KEY"]
        
        # Tentar gerar embedding SEM API key
        with pytest.raises(Exception):
            # Deve lançar exceção, NÃO retornar [0.0, 0.0, ...]
            _get_embedding("test text")
    
    finally:
        # Restaurar API key
        if original_key:
            os.environ["OPENROUTER_API_KEY"] = original_key


# ============================================================================
# RUNNER
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
