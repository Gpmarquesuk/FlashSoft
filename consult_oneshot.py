"""Consulta individual para um modelo especifico."""
import os
import sys
from llm_client import chat

# Modelo a consultar via argumento
if len(sys.argv) < 2:
    print("USO: python consult_oneshot.py <model_id>")
    sys.exit(1)

model_id = sys.argv[1]

question = """EMERGÊNCIA - Fábrica de software com agentes LLM está travada no Planner (0% sucesso):

CONTEXTO ATUAL:
- Planner recebe spec Interview Assistant (4 features, ~800 tokens)
- Deve retornar JSON: {"patches": [...], "test_plan": [...]}
- Implementado JSON Sanitizer com 5 estratégias progressivas
- force_json=False (permite markdown)
- 10 tentativas por execução
- Modelos tentados: Claude Sonnet 4.5, Gemini 2.5 Pro

RESULTADO: 100% falha - "Todas as estratégias de sanitização falharam"
- Sanitizer passa testes isolados mas falha na pipeline
- Erros: "Expecting ',' delimiter: line 14 column 6"

PERGUNTAS:
Q1: Por que LLMs modernos não conseguem gerar JSON válido mesmo com force_json=False (permitindo markdown)?
Q2: O prompt (planner_coder.md) é muito complexo? Deve simplificar?
Q3: Planner deve fazer 1 arquivo por vez em vez de projeto inteiro?
Q4: Causa raiz: (A) Prompt, (B) Spec muito grande, (C) Context window overflow, (D) Capacidade do modelo?
Q5: Solução pragmática IMEDIATA para conseguir 1 execução bem-sucedida?

RESPONDA DE FORMA DIRETA E OBJETIVA (máx 400 tokens)."""

try:
    resp = chat(
        model=model_id,
        messages=[
            {"role": "system", "content": "You are a senior AI-to-AI systems architect with expertise in LLM orchestration, JSON parsing, and agent-based software factories. Provide direct, actionable answers."},
            {"role": "user", "content": question}
        ],
        max_tokens=800,
        temperature=0.2
    )
    
    print(resp)
    
except Exception as e:
    print(f"ERRO: {e}")
    sys.exit(1)
