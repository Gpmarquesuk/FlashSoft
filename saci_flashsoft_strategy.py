#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBATE SACI: INTEGRAÇÃO NA FLASHSOFT + IMPACTO DE MERCADO
==========================================================
Usa SACI EVOLUÍDO para debater:
1. Como integrar SACI EVOLUÍDO na arquitetura FlashSoft
2. Impacto de mercado: FlashSoft com SACI vs. Devin
3. Estratégia de diferenciação e posicionamento
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Garantir UTF-8
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

from saci import run_saci_debate

# ============================================================================
# CONTEXTO: FLASHSOFT + SACI + DEVIN
# ============================================================================

FLASHSOFT_CONTEXT = """
# CONTEXTO: FLASHSOFT

## O QUE É FLASHSOFT?
FlashSoft é uma "fábrica de software autônoma" que transforma especificações (YAML)
em código completo, testado e comitado no GitHub.

**Arquitetura Atual (~2000 linhas Python):**
- **Orchestrator**: Coordena nodes em pipeline linear
- **Nodes especializados**:
  - Planner/Coder: Gera código baseado em specs
  - Tester: Executa testes e valida
  - Reviewer: Revisa qualidade e sugere melhorias
  - Patcher: Aplica correções
- **LLM Router**: Tenta múltiplos models até sucesso (GPT-5, Claude, Gemini, Grok)
- **State Management**: Salva progresso em JSON

**Limitações Atuais:**
- Decisões são tomadas por 1 modelo por vez (sem consenso multi-agent)
- Retry logic é "brute force" (tenta até funcionar, sem análise)
- Não há validação de qualidade via debate (apenas testes unitários)
- Falhas são tratadas reativamente, não preventivamente

**Specs de Exemplo:**
```yaml
name: interview_assistant
description: Assistente de entrevistas com transcrição de áudio
features:
  - Record audio
  - Transcribe with Whisper
  - Generate questions
  - Save interview notes
tech_stack:
  - Python 3.11
  - Flask
  - OpenAI Whisper
```

## SACI EVOLUÍDO

**O que é:**
Sistema de debates multi-agent com:
- Métricas quantitativas (similaridade semântica + votos estruturados)
- Early stopping (threshold 0.75, 3-5 rodadas)
- Rastreabilidade (JSON logs auditáveis)
- ~330 linhas de código, zero frameworks pesados

**Já implementado** (24/10/2025) com consenso de 4 top models.

## DEVIN (Cognition AI)

**Lançado:** Março 2024  
**Modelo:** Agente autônomo para desenvolvimento de software  
**Capacidades:**
- Planejamento de longo prazo (tasks decomposition)
- Execução de código em sandbox seguro
- Debugging interativo
- Navegação em codebases grandes (>100k LOC)
- Integração com ferramentas (terminal, browser, APIs)

**Pontos Fortes:**
- Interface visual (desktop app)
- Suporte a múltiplas linguagens
- Treinado em dados proprietários (engenharia reversa de PRs)
- Autonomia completa (pode trabalhar horas sem supervisão)

**Pontos Fracos (públicos):**
- Custo alto ($500-1000/mês estimado)
- Black-box (não open-source, sem controle sobre decisões)
- Latência alta (minutos para tarefas simples)
- Vendor lock-in (Cognition AI)

**Market Share Estimado (Out/2025):**
- ~5000-10000 empresas usando em produção
- Dominante em startups de AI/tech (early adopters)
"""

# ============================================================================
# QUESTÕES PARA DEBATE
# ============================================================================

QUESTION_INTEGRATION = """
# QUESTÃO: INTEGRAÇÃO SACI NA FLASHSOFT

Como integrar SACI EVOLUÍDO na arquitetura FlashSoft para maximizar impacto?

## OPÇÕES:

### OPÇÃO A: SACI como "Quality Gate" (Validação Final)
- **Onde:** Após Reviewer, antes do commit
- **Como:** Debate entre 4 models se código está "production-ready"
- **Voto:** APPROVE (commita), REJECT (volta para Patcher), ABSTAIN (mais 1 rodada)
- **Benefício:** Zero falsos positivos (código ruim não passa)
- **Custo:** +2-3 minutos por pipeline (4 models debatem)

### OPÇÃO B: SACI como "Decision Maker" (Planejamento)
- **Onde:** Antes do Planner, após ler spec
- **Como:** Debate sobre arquitetura/tech stack ideal
- **Voto:** Escolhe entre 3 opções de arquitetura
- **Benefício:** Decisões consensuais (não arbitrárias)
- **Custo:** +3-5 minutos no início, mas evita refactors

### OPÇÃO C: SACI como "Failure Analyzer" (Debugging)
- **Onde:** Quando Tester falha repetidamente (>3x)
- **Como:** Debate sobre causa-raiz do erro
- **Voto:** Propõe estratégias de fix (3-4 opções)
- **Benefício:** Reduz loops infinitos de retry
- **Custo:** Só ativa em falhas (custo zero em sucesso)

### OPÇÃO D: Híbrida (A + C)
- Quality Gate + Failure Analyzer
- Usa SACI estrategicamente (não em todo pipeline)

### OPÇÃO E: Não integrar
- FlashSoft fica como está (linear, sem consenso)
- SACI vira produto separado

**Vote na melhor opção (A, B, C, D ou E) e justifique.**
**Considere: custo, impacto, complexidade de implementação, ROI.**
"""

QUESTION_MARKET_IMPACT = """
# QUESTÃO: FLASHSOFT COM SACI vs. DEVIN

Como FlashSoft + SACI EVOLUÍDO se compara com Devin?

## ANÁLISE COMPARATIVA

### FlashSoft (Atual - SEM SACI)
- Open-source (controle total)
- Specs declarativas (YAML simples)
- Pipeline linear (1 modelo por vez)
- ~2000 linhas Python (manutenível)
- Custo: apenas API calls (~$0.50-2/pipeline)
- **Limitação:** Sem consenso, decisões arbitrárias

### FlashSoft + SACI EVOLUÍDO (Proposto)
- Open-source + consenso multi-agent
- Decisões validadas por 4 models
- Early stopping (economiza custos)
- Métricas quantitativas (auditável)
- Custo: +$0.30-1/pipeline (debates estratégicos)
- **Vantagem:** Qualidade provável 20-30% maior

### Devin (Cognition AI)
- Black-box proprietário
- Interface visual (GUI desktop)
- Agente autônomo (trabalha sozinho)
- Suporte multi-linguagem
- Custo: $500-1000/mês + API calls
- **Vantagem:** Autonomia completa, debugging visual

## QUESTÃO PARA VOTO:

**Qual afirmação você considera MAIS VERDADEIRA?**

**VOTO A:** FlashSoft+SACI vence Devin em **simplicidade + controle**  
  - Ideal para: Desenvolvedores que querem entender o código gerado
  - Diferencial: Open-source, auditável, sem vendor lock-in
  - Market share potencial: 10-15% (nicho de "anti-black-box")

**VOTO B:** FlashSoft+SACI vence Devin em **custo + ROI**  
  - Ideal para: Startups/PMEs sensíveis a preço
  - Diferencial: $2/pipeline vs $500/mês, sem commitment
  - Market share potencial: 15-25% (devs indie, bootstrapped startups)

**VOTO C:** FlashSoft+SACI perde para Devin em **autonomia**  
  - Devin pode trabalhar 8h sozinho, FlashSoft precisa specs detalhadas
  - Diferencial de Devin: Navegação em codebases, debugging interativo
  - Conclusão: FlashSoft é "ferramenta", Devin é "co-worker"

**VOTO D:** FlashSoft+SACI é **complementar** a Devin (não competidor)  
  - Use Devin para features complexas (40h de dev)
  - Use FlashSoft para tarefas repetitivas (2-4h de dev)
  - Market share: Convivência pacífica (30% overlap, 70% casos distintos)

**Vote na afirmação mais verdadeira (A, B, C ou D) e justifique.**
**Seja brutal: FlashSoft+SACI pode perder feio em alguns aspectos.**
"""

# ============================================================================
# MAIN
# ============================================================================

def main():
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ ERRO: OPENROUTER_API_KEY não encontrada!")
        sys.exit(1)
    
    print("[OK] API Key carregada\n")
    
    # ========================================================================
    # DEBATE 1: INTEGRAÇÃO NA FLASHSOFT
    # ========================================================================
    
    print("=" * 80)
    print("DEBATE 1: COMO INTEGRAR SACI EVOLUÍDO NA FLASHSOFT")
    print("=" * 80 + "\n")
    
    agents = [
        {"name": "Claude Sonnet 4.5", "model": "anthropic/claude-sonnet-4.5", "max_tokens": 4096},
        {"name": "GPT-5 Codex", "model": "openai/gpt-5-codex", "max_tokens": 4096},
        {"name": "Gemini 2.5 PRO", "model": "google/gemini-2.5-pro", "max_tokens": 4096},
        {"name": "Grok 4", "model": "x-ai/grok-4", "max_tokens": 4096}
    ]
    
    result1 = run_saci_debate(
        debate_id="flashsoft_integration",
        question=FLASHSOFT_CONTEXT + "\n\n" + QUESTION_INTEGRATION,
        agents=agents,
        threshold=0.70,  # Mais relaxado (decisão estratégica)
        min_rounds=3,
        max_rounds=5
    )
    
    print("\n" + "=" * 80)
    print("RESULTADO DEBATE 1:")
    print("=" * 80)
    print(f"Score final: {result1['final_score']:.3f}")
    print(f"Convergiu: {'✓ Sim' if result1['converged'] else '✗ Não'}")
    print(f"Rodadas: {result1['total_rounds']}")
    print(f"Decisão consensual: {result1.get('consensual_decision', 'N/A')}")
    
    # Exportar trace
    trace_file1 = Path("logs/saci_flashsoft_integration.json")
    result1['tracer'].export_json(str(trace_file1))
    print(f"  💾 Trace exportado: {trace_file1}\n")
    
    # ========================================================================
    # DEBATE 2: IMPACTO DE MERCADO vs. DEVIN
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("DEBATE 2: FLASHSOFT+SACI vs. DEVIN (IMPACTO DE MERCADO)")
    print("=" * 80 + "\n")
    
    result2 = run_saci_debate(
        debate_id="flashsoft_vs_devin",
        question=FLASHSOFT_CONTEXT + "\n\n" + QUESTION_MARKET_IMPACT,
        agents=agents,
        threshold=0.70,
        min_rounds=3,
        max_rounds=5
    )
    
    print("\n" + "=" * 80)
    print("RESULTADO DEBATE 2:")
    print("=" * 80)
    print(f"Score final: {result2['final_score']:.3f}")
    print(f"Convergiu: {'✓ Sim' if result2['converged'] else '✗ Não'}")
    print(f"Rodadas: {result2['total_rounds']}")
    print(f"Decisão consensual: {result2.get('consensual_decision', 'N/A')}")
    
    # Exportar trace
    trace_file2 = Path("logs/saci_flashsoft_vs_devin.json")
    result2['tracer'].export_json(str(trace_file2))
    print(f"  💾 Trace exportado: {trace_file2}\n")
    
    # ========================================================================
    # SÍNTESE FINAL
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("SÍNTESE: ESTRATÉGIA FLASHSOFT + SACI")
    print("=" * 80 + "\n")
    
    synthesis = {
        "date": datetime.now().isoformat(),
        "debate1_integration": {
            "score": result1["final_score"],
            "converged": result1["converged"],
            "rounds": result1["total_rounds"],
            "decision": result1.get("consensual_decision"),
            "trajectory": result1["score_trajectory"]
        },
        "debate2_market_impact": {
            "score": result2["final_score"],
            "converged": result2["converged"],
            "rounds": result2["total_rounds"],
            "decision": result2.get("consensual_decision"),
            "trajectory": result2["score_trajectory"]
        }
    }
    
    synthesis_file = Path("logs/saci_flashsoft_SYNTHESIS.json")
    with open(synthesis_file, "w", encoding="utf-8") as f:
        json.dump(synthesis, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Síntese completa salva em: {synthesis_file}")
    print(f"\n📊 Trajetórias de convergência:")
    print(f"  Integração: {[f'{s:.2f}' for s in result1['score_trajectory']]}")
    print(f"  vs. Devin:  {[f'{s:.2f}' for s in result2['score_trajectory']]}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Debate interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERRO FATAL: {type(e).__name__}")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
