# -*- coding: utf-8 -*-
"""Teste do prompt SACI para identificar problema de timeout"""
import time
from llm_client import chat

# Carregar as variáveis do saci_implementation_strategy.py
exec(open('saci_implementation_strategy.py', encoding='utf-8').read().split('def consult')[0])

print("=" * 80)
print("TESTE: Claude Sonnet 4.5 + PROMPT_ROUND1")
print("=" * 80)
print(f"\nTamanho do prompt: {len(PROMPT_ROUND1)} chars (~{len(PROMPT_ROUND1)//4} tokens)")
print(f"Max tokens solicitados: 4096\n")

start = time.time()
try:
    response = chat(
        model='anthropic/claude-sonnet-4.5',
        system='You are Claude Sonnet 4.5, specialist in deep reasoning.',
        user=PROMPT_ROUND1,
        temperature=0.2,
        max_tokens=4096
    )
    elapsed = time.time() - start
    print(f"✅ SUCCESS ({elapsed:.1f}s)")
    print(f"   Resposta: {len(response)} chars (~{len(response)//4} tokens)")
    print(f"\nPrimeiros 500 chars:\n{response[:500]}...")
except Exception as e:
    elapsed = time.time() - start
    print(f"❌ FAILED ({elapsed:.1f}s)")
    print(f"   Erro: {type(e).__name__} - {str(e)[:200]}")
