#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CONSULTA EMERGENCIAL À JUNTA DE ESPECIALISTAS
Conforme ordenado pelo usuário: Grok 4, Gemini 2.5 Pro, GPT-5
"""
import os
from pathlib import Path

# Força load do .env ANTES de importar llm_client
from dotenv import load_dotenv
load_dotenv(override=True)

# Verifica se carregou
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise RuntimeError("OPENROUTER_API_KEY ainda ausente após load_dotenv!")

print(f"OK - API Key carregada: {api_key[:15]}...")

from llm_client import chat

# MODELOS MAIS AVANÇADOS DA OPENAI (conforme solicitado)
models = {
    'grok4': 'x-ai/grok-4',  # Grok 4
    'gemini25': 'google/gemini-2.5-flash-preview-09-2025',  # Gemini 2.5
    'o3pro': 'openai/o3-pro',  # O3 Pro (MAIS AVANÇADO OpenAI)
    'o1pro': 'openai/o1-pro',  # O1 Pro (reasoning)
    'gpt5codex': 'openai/gpt-5-codex'  # GPT-5 Codex (especializado em código)
}

system = """Você é um arquiteto sênior de sistemas AI-to-AI. 
Responda de forma DIRETA e TÉCNICA."""

user_prompt = """SITUAÇÃO CRÍTICA:

1. Implementamos JSON Sanitizer com 5 estratégias (direct parse, markdown extraction, common fixes, fuzzy extraction, structural repair)
2. Aumentamos tentativas de 3 para 10
3. Mudamos force_json=True para force_json=False (permitir markdown)
4. **RESULTADO: AINDA FALHA 100%!** Mensagem: "❌ Todas as estratégias de sanitização falharam"

PERGUNTA 1: Por que um LLM moderno (Claude Sonnet 4, Gemini 2.5 Pro) NÃO consegue gerar JSON válido mesmo com force_json=False? O que está acontecendo?

PERGUNTA 2: O prompt está muito complexo? Devemos simplificar drasticamente?

PERGUNTA 3: O Planner está tentando gerar patches para TODO o projeto de uma vez? Devemos quebrar em tarefas menores (1 arquivo por vez)?

PERGUNTA 4: Qual a causa raiz mais provável: (A) Prompt mal estruturado, (B) Spec muito complexo, (C) Context window overflow, (D) Modelo não segue instruções JSON?

PERGUNTA 5: **SOLUÇÃO IMEDIATA:** O que fazer AGORA para conseguir 1 execução bem-sucedida? Seja específico e pragmático.

Responda objetivamente com números (Q1, Q2, etc).
"""

print("\n" + "="*80)
print("CONSULTA À JUNTA DE ESPECIALISTAS - EMERGÊNCIA")
print("="*80 + "\n")

for name, model in models.items():
    try:
        print(f"\n>>> {name.upper()} ({model})")
        print("-" * 80)
        
        response = chat(
            model, 
            system, 
            user_prompt, 
            max_tokens=1500,  # Mais tokens para resposta completa
            temperature=0.2  # Baixa temp para respostas focadas
        )
        
        print(response)
        print("-" * 80)
        
        # Salvar
        output_file = Path(f'logs/consult_emergency_{name}.txt')
        output_file.write_text(response, encoding='utf-8')
        print(f"OK - Salvo em: {output_file}\n")
        
    except Exception as e:
        print(f"ERRO: {e}")
        print("-" * 80 + "\n")

print("\n" + "="*80)
print("CONSULTA CONCLUÍDA")
print("="*80)
