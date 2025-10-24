#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embedding Client - OpenAI
=========================

Cliente dedicado para interagir com a API de embeddings da OpenAI.

Responsabilidades:
------------------
1. Carregar a chave da API da OpenAI do ambiente.
2. Fornecer uma função para gerar embeddings de texto.
3. Lidar com erros específicos da API da OpenAI.

Uso:
----
    from embedding_client import get_embedding
    
    try:
        vector = get_embedding("Este é um texto de exemplo.")
        print(f"Vetor gerado: {len(vector)} dimensões")
    except Exception as e:
        print(f"Erro ao gerar embedding: {e}")

Autor: FlashSoft Team
Data: 24/10/2025
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# ============================================================================
# CONFIGURAÇÃO DO CLIENTE OPENAI
# ============================================================================

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("A variável de ambiente OPENAI_API_KEY não foi definida.")

try:
    client = OpenAI(api_key=api_key)
except Exception as e:
    raise RuntimeError(f"Falha ao inicializar o cliente OpenAI: {e}")

# Modelo de embedding recomendado pela OpenAI (custo-benefício)
EMBEDDING_MODEL = "text-embedding-3-small"

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> list[float]:
    """
    Gera um vetor de embedding para um determinado texto usando a API da OpenAI.

    Args:
        text: O texto de entrada a ser convertido em embedding.
        model: O modelo de embedding a ser usado.

    Returns:
        Uma lista de floats representando o vetor de embedding.

    Raises:
        Exception: Se a chamada da API falhar.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("O texto de entrada não pode ser vazio.")

    try:
        # Substitui caracteres de nova linha para evitar problemas com a API
        text = text.replace("\n", " ")
        
        response = client.embeddings.create(input=[text], model=model)
        
        if response.data and response.data[0].embedding:
            return response.data[0].embedding
        else:
            raise RuntimeError("A resposta da API de embeddings não continha dados válidos.")
            
    except Exception as e:
        # Adiciona mais contexto ao erro antes de relançá-lo
        print(f"Erro na chamada da API OpenAI para o modelo '{model}': {e}")
        raise

# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("Testando o cliente de embeddings da OpenAI...")
    
    test_text_1 = "O cachorro late para a lua."
    test_text_2 = "O cão uiva para o satélite natural da Terra."
    test_text_3 = "O mercado de ações subiu hoje."

    try:
        print(f"\nGerando embedding para: '{test_text_1}'")
        vector1 = get_embedding(test_text_1)
        print(f"✅ Sucesso! Dimensões do vetor: {len(vector1)}")

        print(f"\nGerando embedding para: '{test_text_2}'")
        vector2 = get_embedding(test_text_2)
        print(f"✅ Sucesso! Dimensões do vetor: {len(vector2)}")

        print(f"\nGerando embedding para: '{test_text_3}'")
        vector3 = get_embedding(test_text_3)
        print(f"✅ Sucesso! Dimensões do vetor: {len(vector3)}")

        # Teste de similaridade (requer numpy e scikit-learn)
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np

            sim_1_2 = cosine_similarity([vector1], [vector2])[0][0]
            sim_1_3 = cosine_similarity([vector1], [vector3])[0][0]

            print("\n--- Teste de Similaridade ---")
            print(f"Similaridade entre texto 1 e 2: {sim_1_2:.4f} (Esperado: ALTA)")
            print(f"Similaridade entre texto 1 e 3: {sim_1_3:.4f} (Esperado: BAIXA)")
            
            assert sim_1_2 > 0.7, "A similaridade entre textos sinônimos deveria ser alta."
            assert sim_1_3 < 0.5, "A similaridade entre textos distintos deveria ser baixa."
            
            print("\n✅ Testes de similaridade passaram com sucesso!")

        except ImportError:
            print("\n⚠️ Para rodar o teste de similaridade, instale scikit-learn e numpy:")
            print("   pip install scikit-learn numpy")

    except Exception as e:
        print(f"\n❌ Teste falhou: {e}")
        print("   Verifique se a sua chave OPENAI_API_KEY está correta no arquivo .env")

