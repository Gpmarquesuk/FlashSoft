#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTE SACI v2.0.1 - Validação Pós-Correções
============================================

Executa 3 debates para validar:
1. SACI 1.0 vs SACI 2.0 - Comparação
2. Como reduzir latência na SACI 2.0
3. Como implementar melhor UI na SACI 2.0

Objetivo: Verificar se correções consensuais funcionaram.
"""

import os
import sys
import json
from datetime import datetime

# Configurar environment
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Importar SACI 2.0
from saci import run_saci_debate

print("\n" + "="*80)
print("🧪 TESTE SACI v2.0.1 - PÓS-CORREÇÕES CONSENSUAIS")
print("="*80)
print(f"\nData: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Objetivo: Validar correções de logging, retry e embeddings\n")

# Modelos SACI (FIXOS)
SACI_MODELS = [
    "anthropic/claude-sonnet-4.5",
    "openai/gpt-5-codex",
    "google/gemini-2.5-pro",
    "x-ai/grok-4"
]

# ============================================================================
# DEBATE 1: SACI 1.0 vs SACI 2.0
# ============================================================================

print("\n" + "="*80)
print("📊 DEBATE 1: SACI 1.0 vs SACI 2.0")
print("="*80 + "\n")

debate1_problema = """
SACI 1.0 vs SACI 2.0: Qual versão usar em produção?

Contexto:
- SACI 1.0: Simples, testada, sem métricas quantitativas
- SACI 2.0: Métricas semânticas, early stopping, mais complexa

Questão: Baseado nas características de cada versão, qual recomendação 
vocês fazem para uso em produção AGORA (outubro 2025)?

Opções:
A) Usar SACI 1.0 (estável, simples)
B) Usar SACI 2.0 (features avançadas)
C) Usar 1.0 para casos simples, 2.0 para casos complexos
D) Esperar mais testes antes de decidir

Vote e justifique sua escolha.
"""

debate1_contexto = """
SACI 1.0:
- ✅ Estável e testada
- ✅ Votos por keywords (funciona)
- ✅ Simples (300 linhas)
- ❌ Sem métricas semânticas
- ❌ Sem early stopping inteligente
- ❌ Todas rodadas executadas sempre

SACI 2.0.1 (Pós-correções):
- ✅ Métricas semânticas (embeddings)
- ✅ Early stopping (economiza custo)
- ✅ Logging adequado
- ✅ Rastreabilidade JSON
- ❌ Mais complexa (~500 linhas)
- ❌ Precisa validação em produção
- ⚠️ Embeddings podem estar com problemas
"""

try:
    print("⏳ Iniciando debate 1...")
    resultado1 = run_saci_debate(
        problema=debate1_problema,
        contexto=debate1_contexto,
        models=SACI_MODELS,
        max_rounds=3,
        convergence_threshold=0.70,
        output_file="logs/saci_test_v1_vs_v2.json"
    )
    
    print("\n✅ DEBATE 1 CONCLUÍDO")
    print(f"Consenso: {resultado1.get('converged', False)}")
    print(f"Score final: {resultado1.get('final_score', 0):.3f}")
    print(f"Rodadas: {len(resultado1.get('rounds', []))}")
    
except Exception as e:
    print(f"\n❌ ERRO NO DEBATE 1: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# DEBATE 2: Como reduzir latência SACI 2.0
# ============================================================================

print("\n" + "="*80)
print("⚡ DEBATE 2: Como reduzir latência na SACI 2.0")
print("="*80 + "\n")

debate2_problema = """
Como reduzir latência na SACI 2.0 sem perder qualidade?

Contexto:
- SACI 2.0 é mais lenta que 1.0 (embeddings + métricas)
- Cada rodada: 4 LLM calls + 4 embeddings
- Latência típica: 30-60s por rodada
- Usuários querem respostas < 2 minutos total

Questão: Qual estratégia priorizar para reduzir latência?

Opções:
A) Cache agressivo de embeddings
B) Paralelizar chamadas LLM + embeddings
C) Reduzir max_rounds (3 → 2)
D) Early stopping mais agressivo (threshold 0.65)
E) Usar modelos mais rápidos (sem perder qualidade)

Vote na melhor estratégia e justifique.
"""

debate2_contexto = """
Trade-offs conhecidos:
- Cache: Reduz embeddings, mas pode comprometer novidade
- Paralelização: Reduz latência total, aumenta custo instantâneo
- Menos rounds: Pode não convergir
- Threshold menor: Pode aceitar consenso fraco
- Modelos rápidos: Podem perder qualidade

Meta: < 2 minutos total, manter qualidade de consenso
"""

try:
    print("⏳ Iniciando debate 2...")
    resultado2 = run_saci_debate(
        problema=debate2_problema,
        contexto=debate2_contexto,
        models=SACI_MODELS,
        max_rounds=3,
        convergence_threshold=0.70,
        output_file="logs/saci_test_latency.json"
    )
    
    print("\n✅ DEBATE 2 CONCLUÍDO")
    print(f"Consenso: {resultado2.get('converged', False)}")
    print(f"Score final: {resultado2.get('final_score', 0):.3f}")
    print(f"Rodadas: {len(resultado2.get('rounds', []))}")
    
except Exception as e:
    print(f"\n❌ ERRO NO DEBATE 2: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# DEBATE 3: Melhor UI para SACI 2.0
# ============================================================================

print("\n" + "="*80)
print("🎨 DEBATE 3: Melhor UI para SACI 2.0")
print("="*80 + "\n")

debate3_problema = """
Qual a melhor interface de usuário para SACI 2.0?

Contexto:
- SACI 2.0 gera muito contexto: votos, scores, similaridade, logs
- Usuários precisam entender convergência e tomar decisões
- Deve funcionar em terminal E web

Questão: Qual abordagem de UI priorizar?

Opções:
A) CLI rica (rich/typer) com progress bars e tabelas
B) Web UI (Streamlit/Gradio) com gráficos interativos
C) Dashboard (React/Vue) profissional
D) JSON API + múltiplas UIs (desacoplamento)
E) Terminal simples + logs JSON (atual)

Vote considerando:
- Facilidade de implementação
- Experiência do usuário
- Manutenibilidade
- Tempo de desenvolvimento
"""

debate3_contexto = """
Requisitos:
- Mostrar progresso do debate em tempo real
- Visualizar scores de convergência
- Exibir votos de cada modelo
- Permitir intervenção humana (opcional)
- Exportar resultados

Restrições:
- Equipe pequena (1-2 devs)
- Tempo limitado (1-2 semanas)
- Deve ser fácil de manter

Público:
- Desenvolvedores técnicos
- Product managers
- Stakeholders não-técnicos (eventualmente)
"""

try:
    print("⏳ Iniciando debate 3...")
    resultado3 = run_saci_debate(
        problema=debate3_problema,
        contexto=debate3_contexto,
        models=SACI_MODELS,
        max_rounds=3,
        convergence_threshold=0.70,
        output_file="logs/saci_test_ui.json"
    )
    
    print("\n✅ DEBATE 3 CONCLUÍDO")
    print(f"Consenso: {resultado3.get('converged', False)}")
    print(f"Score final: {resultado3.get('final_score', 0):.3f}")
    print(f"Rodadas: {len(resultado3.get('rounds', []))}")
    
except Exception as e:
    print(f"\n❌ ERRO NO DEBATE 3: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# RESUMO FINAL
# ============================================================================

print("\n" + "="*80)
print("📊 RESUMO DOS TESTES SACI v2.0.1")
print("="*80 + "\n")

print("RESULTADOS:")
print("-" * 80)

try:
    print(f"\n1️⃣  SACI 1.0 vs 2.0:")
    print(f"   Consenso: {'✅ SIM' if resultado1.get('converged') else '❌ NÃO'}")
    print(f"   Score: {resultado1.get('final_score', 0):.3f}")
    print(f"   Rodadas: {len(resultado1.get('rounds', []))}")
    if resultado1.get('converged'):
        print(f"   Decisão: [Ver logs/saci_test_v1_vs_v2.json]")
except:
    print("\n1️⃣  SACI 1.0 vs 2.0: ❌ FALHOU")

try:
    print(f"\n2️⃣  Redução de latência:")
    print(f"   Consenso: {'✅ SIM' if resultado2.get('converged') else '❌ NÃO'}")
    print(f"   Score: {resultado2.get('final_score', 0):.3f}")
    print(f"   Rodadas: {len(resultado2.get('rounds', []))}")
    if resultado2.get('converged'):
        print(f"   Estratégia: [Ver logs/saci_test_latency.json]")
except:
    print("\n2️⃣  Redução de latência: ❌ FALHOU")

try:
    print(f"\n3️⃣  Melhor UI:")
    print(f"   Consenso: {'✅ SIM' if resultado3.get('converged') else '❌ NÃO'}")
    print(f"   Score: {resultado3.get('final_score', 0):.3f}")
    print(f"   Rodadas: {len(resultado3.get('rounds', []))}")
    if resultado3.get('converged'):
        print(f"   UI escolhida: [Ver logs/saci_test_ui.json]")
except:
    print("\n3️⃣  Melhor UI: ❌ FALHOU")

print("\n" + "="*80)
print("📁 LOGS SALVOS EM:")
print("   - logs/saci_test_v1_vs_v2.json")
print("   - logs/saci_test_latency.json")
print("   - logs/saci_test_ui.json")
print("="*80 + "\n")

print("🔬 VALIDAÇÃO DAS CORREÇÕES:")
print("-" * 80)
print("Verifique nos logs se:")
print("  1. Similaridade semântica > 0.0 (não zerada)")
print("  2. Logging aparece corretamente")
print("  3. Early stopping funciona (se score > 0.70)")
print("  4. Votos são extraídos corretamente")
print("\n")
