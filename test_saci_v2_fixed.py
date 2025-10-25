#!/usr/bin/env python3
"""
Teste integrado da SACI v2.0.1 com correções consensuais (4/4 models).

Executa 3 debates reais para validar:
1. Logging adequado (logger.critical)
2. Retry logic (max_retries=2)
3. Timeout aumentado (30s)
4. Embeddings funcionando (não retornam 0.0)
5. Early stopping operacional

Data: 2025-01-24
Versão: SACI v2.0.1 (pós-correções)
"""

from saci import run_saci_debate
from datetime import datetime

print("="*80)
print("TESTE SACI v2.0.1 - POS-CORRECOES CONSENSUAIS")
print("="*80)
print(f"\nData: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Objetivo: Validar correcoes de logging, retry e embeddings\n")

# ============================================================================
# DEBATE 1: SACI 1.0 vs SACI 2.0
# ============================================================================

print("="*80)
print("DEBATE 1: SACI 1.0 vs SACI 2.0")
print("="*80 + "\n")

try:
    print("Iniciando debate 1...\n")
    resultado1 = run_saci_debate(
        debate_id="saci_test_v1_vs_v2",
        question="""SACI 1.0 vs SACI 2.0: Qual usar em produção?

SACI 1.0:
- Keyword voting simples
- Sem embeddings
- ~300 linhas de código
- Sem early stopping
- Timeout 10s

SACI 2.0:
- OpenAI embeddings
- Convergence metrics
- ~500 linhas
- Early stopping
- Timeout 30s, retry logic

OPTIONS:
A) SACI 1.0 - simplicidade e confiabilidade
B) SACI 2.0 - métricas semânticas superiores
C) Usar 1.0 em produção, 2.0 experimental
D) Fundir ambas numa v3.0 híbrida
E) Deprecar 1.0, investir só em 2.0

Vote clearly (VOTE: A/B/C/D/E) and justify your choice.""",
        agents=[
            {"name": "Claude Sonnet", "model": "anthropic/claude-sonnet-4.5", "max_tokens": 4096},
            {"name": "GPT-5 Codex", "model": "openai/gpt-5-codex", "max_tokens": 4096},
            {"name": "Gemini Pro", "model": "google/gemini-2.5-pro", "max_tokens": 4096},
            {"name": "Grok-4", "model": "x-ai/grok-4", "max_tokens": 4096}
        ],
        threshold=0.70,
        min_rounds=2,
        max_rounds=3
    )
    
    print("\nDEBATE 1 CONCLUIDO")
    print(f"Convergiu: {resultado1.get('converged', False)}")
    print(f"Score final: {resultado1.get('final_convergence_score', 0):.3f}")
    print(f"Rodadas: {resultado1.get('total_rounds', 0)}")
    
except Exception as e:
    print(f"\nERRO NO DEBATE 1: {e}")
    import traceback
    traceback.print_exc()
    resultado1 = None

# ============================================================================
# DEBATE 2: Como reduzir latência SACI 2.0
# ============================================================================

print("\n" + "="*80)
print("⚡ DEBATE 2: Como reduzir latência na SACI 2.0")
print("="*80 + "\n")

try:
    print("⏳ Iniciando debate 2...\n")
    resultado2 = run_saci_debate(
        debate_id="saci_test_latency",
        question="""Como reduzir latência na SACI 2.0 sem perder qualidade?

Contexto:
- SACI 2.0 é mais lenta que 1.0 (embeddings + métricas)
- Cada rodada: 4 LLM calls + 4 embeddings
- Latência típica: 30-60s por rodada
- Usuários querem respostas < 2 minutos total

OPTIONS:
A) Cache agressivo de embeddings
B) Chamar LLMs em paralelo (asyncio)
C) Usar embeddings locais (sentence-transformers)
D) Reduzir max_tokens dos modelos
E) Implementar timeout adaptivo por rodada

Vote clearly (VOTE: A/B/C/D/E) and justify.""",
        agents=[
            {"name": "Claude Sonnet", "model": "anthropic/claude-sonnet-4.5", "max_tokens": 4096},
            {"name": "GPT-5 Codex", "model": "openai/gpt-5-codex", "max_tokens": 4096},
            {"name": "Gemini Pro", "model": "google/gemini-2.5-pro", "max_tokens": 4096},
            {"name": "Grok-4", "model": "x-ai/grok-4", "max_tokens": 4096}
        ],
        threshold=0.70,
        min_rounds=2,
        max_rounds=3
    )
    
    print("\n✅ DEBATE 2 CONCLUÍDO")
    print(f"Convergiu: {resultado2.get('converged', False)}")
    print(f"Score final: {resultado2.get('final_convergence_score', 0):.3f}")
    print(f"Rodadas: {resultado2.get('total_rounds', 0)}")
    
except Exception as e:
    print(f"\n❌ ERRO NO DEBATE 2: {e}")
    import traceback
    traceback.print_exc()
    resultado2 = None

# ============================================================================
# DEBATE 3: Melhor UI para SACI 2.0
# ============================================================================

print("\n" + "="*80)
print("🎨 DEBATE 3: Melhor UI para SACI 2.0")
print("="*80 + "\n")

try:
    print("⏳ Iniciando debate 3...\n")
    resultado3 = run_saci_debate(
        debate_id="saci_test_ui",
        question="""Qual a melhor UI para SACI 2.0 em produção?

Contexto:
- SACI 2.0 tem métricas ricas (scores, convergence, rounds)
- Usuários precisam confiar no resultado
- Debates podem ser longos (3-5 rodadas)
- Importante: transparência + rastreabilidade

OPTIONS:
A) CLI simples com progress bar
B) Web UI com React + gráficos em tempo real
C) Jupyter widgets interativos
D) Terminal UI (rich/textual) com live updates
E) API REST + webhook para integração

Vote clearly (VOTE: A/B/C/D/E) and justify.""",
        agents=[
            {"name": "Claude Sonnet", "model": "anthropic/claude-sonnet-4.5", "max_tokens": 4096},
            {"name": "GPT-5 Codex", "model": "openai/gpt-5-codex", "max_tokens": 4096},
            {"name": "Gemini Pro", "model": "google/gemini-2.5-pro", "max_tokens": 4096},
            {"name": "Grok-4", "model": "x-ai/grok-4", "max_tokens": 4096}
        ],
        threshold=0.70,
        min_rounds=2,
        max_rounds=3
    )
    
    print("\n✅ DEBATE 3 CONCLUÍDO")
    print(f"Convergiu: {resultado3.get('converged', False)}")
    print(f"Score final: {resultado3.get('final_convergence_score', 0):.3f}")
    print(f"Rodadas: {resultado3.get('total_rounds', 0)}")
    
except Exception as e:
    print(f"\n❌ ERRO NO DEBATE 3: {e}")
    import traceback
    traceback.print_exc()
    resultado3 = None

# ============================================================================
# RESUMO DOS TESTES
# ============================================================================

print("\n" + "="*80)
print("📊 RESUMO DOS TESTES SACI v2.0.1")
print("="*80 + "\n")

print("RESULTADOS:")
print("-"*80)

# Debate 1
print("\n1️⃣  SACI 1.0 vs 2.0:")
if resultado1:
    print(f"   ✅ Convergiu: {resultado1.get('converged', False)}")
    print(f"   📊 Score: {resultado1.get('final_convergence_score', 0):.3f}")
    print(f"   🔄 Rodadas: {resultado1.get('total_rounds', 0)}")
    
    # Extrai scores de cada rodada
    if 'trajectory' in resultado1:
        print(f"   📈 Trajetória: {[round(s, 2) for s in resultado1['trajectory']]}")
else:
    print("   ❌ FALHOU")

# Debate 2
print("\n2️⃣  Redução de latência:")
if resultado2:
    print(f"   ✅ Convergiu: {resultado2.get('converged', False)}")
    print(f"   📊 Score: {resultado2.get('final_convergence_score', 0):.3f}")
    print(f"   🔄 Rodadas: {resultado2.get('total_rounds', 0)}")
    
    if 'trajectory' in resultado2:
        print(f"   📈 Trajetória: {[round(s, 2) for s in resultado2['trajectory']]}")
else:
    print("   ❌ FALHOU")

# Debate 3
print("\n3️⃣  Melhor UI:")
if resultado3:
    print(f"   ✅ Convergiu: {resultado3.get('converged', False)}")
    print(f"   📊 Score: {resultado3.get('final_convergence_score', 0):.3f}")
    print(f"   🔄 Rodadas: {resultado3.get('total_rounds', 0)}")
    
    if 'trajectory' in resultado3:
        print(f"   📈 Trajetória: {[round(s, 2) for s in resultado3['trajectory']]}")
else:
    print("   ❌ FALHOU")

print("\n" + "="*80)
print("🔬 VALIDAÇÃO DAS CORREÇÕES:")
print("-"*80)
print("Verifique se:")
print("  1. ✅ Similaridade semântica > 0.0 (não zerada)")
print("  2. ✅ Logging aparece corretamente")
print("  3. ✅ Early stopping funciona (se score > 0.70)")
print("  4. ✅ Votos são extraídos corretamente")
print("  5. ✅ Exceptions propagam (não mais silent fallback)")
print("="*80)
