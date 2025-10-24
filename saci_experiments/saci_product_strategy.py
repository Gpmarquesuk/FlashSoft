#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SACI PRODUCT STRATEGY DEBATE
=============================
Objetivo: Definir estratégia de produto para SACI EVOLUÍDO
- SACI EVOLUÍDO = Implementação consensual (Fases 1+2) sem LangGraph/AutoGen
- Deliverables: Metodologia de implementação + Diferenciação de mercado + Impacto

Rodadas:
1. ARQUITETURA & METODOLOGIA: Como construir (módulos, patterns, tests)
2. ANÁLISE COMPETITIVA: Como se diferencia (vs AutoGen, LangChain, CrewAI)
3. ESTRATÉGIA DE GO-TO-MARKET: Como impactar o mercado de AI agents
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Garantir UTF-8
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

from llm_client import chat

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

AGENTS = [
    {
        "name": "Claude Sonnet 4.5",
        "model": "anthropic/claude-sonnet-4.5",
        "specialty": "System architecture, technical implementation patterns",
        "max_tokens": 8192
    },
    {
        "name": "GPT-5 Codex",
        "model": "openai/gpt-5-codex",
        "specialty": "Code design, testing strategies, developer experience",
        "max_tokens": 4096
    },
    {
        "name": "Gemini 2.5 PRO",
        "model": "google/gemini-2.5-pro",
        "specialty": "Market analysis, competitive positioning, business strategy",
        "max_tokens": 8192
    },
    {
        "name": "Grok 4",
        "model": "x-ai/grok-4",
        "specialty": "Go-to-market strategy, ecosystem impact, adoption barriers",
        "max_tokens": 8192
    }
]

OUTPUT_DIR = Path("logs")
OUTPUT_DIR.mkdir(exist_ok=True)

DELAY_BETWEEN_CALLS = 5  # segundos

# ============================================================================
# CONTEXTO: SACI EVOLUÍDO (Consenso Fases 1+2)
# ============================================================================

SACI_EVOLVED_CONTEXT = """
# CONTEXTO: SACI EVOLUÍDO

## O QUE É SACI EVOLUÍDO?
SACI EVOLUÍDO é a implementação consensual obtida através de debate entre 4 top models
(Claude, GPT-5 Codex, Gemini, Grok 4) em 24/10/2025.

**Decisão Consensual (4/4 agentes, confiança 80-95%):**
- Implementar APENAS Fases 1+2 da evolução
- NÃO usar LangGraph ou AutoGen (frameworks pesados)
- Adicionar ~300 linhas ao código atual (~700 linhas)
- Total: ~1000 linhas de código Python

## FEATURES CONSENSUAIS

### Feature 1: Métricas Quantitativas Simples (~50-150 linhas)
- Similaridade semântica via embeddings OpenAI
- Score de convergência objetivo (0-1)
- Extração de votos estruturados (parsing de JSON)
- **Benefício:** Convergência objetiva vs. qualitativa pura
- **Dependências:** Nenhuma nova (usa OpenAI SDK existente)

### Feature 2: Early Stopping com Threshold (~90-120 linhas)
- Rodadas dinâmicas (máximo 5, mínimo 3)
- Para se score ≥ 70-75%
- Detecta consenso real vs. falso consenso
- **Benefício:** Economia de custos (API calls), adaptabilidade
- **Dependências:** Nenhuma

### Feature 3: Rastreabilidade Estruturada (~80-150 linhas)
- Logs em JSON com scores por rodada
- Métricas exportáveis para análise
- Auditoria quantitativa + textos interpretativos
- **Benefício:** Transparência, debugging, compliance
- **Dependências:** Nenhuma (JSON nativo)

## ARQUITETURA PROPOSTA

```
saci_implementation_strategy.py (atual - 700 linhas)
├── debate_round() # mantém lógica atual
└── NOVOS MÓDULOS:
    ├── convergence_metrics.py (150 linhas)
    │   ├── compute_semantic_similarity(texts) → float 0-1
    │   ├── extract_structured_votes(responses) → dict
    │   └── calculate_convergence_score(round_results) → float
    ├── round_manager.py (100 linhas)
    │   ├── run_dynamic_rounds(max=5, threshold=0.75)
    │   └── should_stop_early(score, round_num) → bool
    └── trace_logger.py (80 linhas)
        ├── log_round(round_num, results, score)
        └── export_json()
```

## COMPARAÇÃO: ATUAL vs. EVOLUÍDO vs. IDEAL

| Aspecto | ATUAL | EVOLUÍDO (Fases 1+2) | IDEAL (LangGraph+AutoGen) |
|---------|-------|----------------------|---------------------------|
| Linhas de código | 700 | 1000 (+300) | 2700 (+2000) |
| Dependências | OpenAI SDK | OpenAI SDK | LangGraph, AutoGen, sentence-transformers |
| Convergência | Qualitativa | Híbrida (Qual + 2 métricas) | Quantitativa (3+ métricas) |
| Rodadas | 3 fixas | 3-5 dinâmicas | 1-10 adaptativas |
| Complexidade | Baixa | Média | Alta |
| Tempo dev | - | 2-4 dias | 2-3 semanas |
| Benefícios capturados | - | 65-80% do ideal | 100% |
| Complexidade adicionada | - | 15-40% do ideal | 100% |

## O QUE NÃO FAZER (Consenso Unânime)
1. **LangGraph/AutoGen** - Complexidade >> Benefício
2. **Voting explícito forçado** - Quebra naturalidade
3. **Pesos multi-dimensionais fixos** - Over-engineering
4. **Critique validation automática** - NLP complexo, ROI incerto
5. **Banco de dados** - JSON files são suficientes

## LIMITAÇÕES ATUAIS RESOLVIDAS
- ❌ **Antes:** Convergência puramente subjetiva (prompt-based)
  ✅ **Depois:** Score numérico 0-1 + votos estruturados
  
- ❌ **Antes:** 3 rodadas fixas (desperdício ou insuficiente)
  ✅ **Depois:** 3-5 rodadas dinâmicas (early stopping)
  
- ❌ **Antes:** Rastreabilidade só via textos longos
  ✅ **Depois:** JSON estruturado + métricas exportáveis

## PÚBLICO-ALVO
- Desenvolvedores Python que precisam de debates multi-agent
- Empresas que querem consenso em decisões técnicas
- Equipes que não querem frameworks pesados (LangChain, AutoGen)
- Projetos que valorizam simplicidade + interpretabilidade
"""

# ============================================================================
# PROMPTS DAS RODADAS
# ============================================================================

ROUND1_PROMPT = """
# RODADA 1: ARQUITETURA & METODOLOGIA DE IMPLEMENTAÇÃO

Você é {specialty}.

## CONTEXTO
{context}

## SUA MISSÃO
Definir a **metodologia detalhada de implementação** do SACI EVOLUÍDO.

## DELIVERABLES OBRIGATÓRIOS (≈400 palavras)

### 1. ARQUITETURA TÉCNICA DETALHADA (150 palavras)
- Estrutura de módulos (onde cada feature vai)
- Interfaces entre componentes (funções públicas, contracts)
- Padrões de design (classes vs. funções puras, state management)
- Exemplo de código (pseudo-code) para a integração principal

### 2. METODOLOGIA DE IMPLEMENTAÇÃO (150 palavras)
- Ordem de implementação (qual feature primeiro e por quê)
- Estratégia de testing (unit tests, integration tests, fixtures)
- Pontos de extensibilidade (onde adicionar features futuras)
- Trade-offs técnicos críticos (performance vs. simplicidade, etc.)

### 3. RISCO & MITIGAÇÃO (100 palavras)
- Top 3 riscos técnicos (ex: OpenAI embeddings lentos, false positives)
- Estratégias de mitigação concretas
- Fallbacks (o que fazer se feature X falhar)

## RESTRIÇÕES
- Máximo 300 linhas de código novo
- Zero dependências pesadas (>100MB)
- Manter simplicidade do código atual (legível, debuggável)

Responda de forma estruturada, técnica e CONCRETA.
"""

ROUND2_PROMPT = """
# RODADA 2: ANÁLISE COMPETITIVA & DIFERENCIAÇÃO

Você é {specialty}.

## CONTEXTO
{context}

## RODADA ANTERIOR (Arquitetura)
{previous_round}

## SUA MISSÃO
Analisar como **SACI EVOLUÍDO se diferencia** dos produtos existentes no mercado.

## DELIVERABLES OBRIGATÓRIOS (≈450 palavras)

### 1. ANÁLISE COMPETITIVA (200 palavras)
Compare SACI EVOLUÍDO vs. principais concorrentes:

**AutoGen (Microsoft)**
- O que AutoGen faz melhor?
- Onde SACI EVOLUÍDO vence?
- Overlap de funcionalidades (%)

**LangGraph (LangChain)**
- O que LangGraph faz melhor?
- Onde SACI EVOLUÍDO vence?
- Overlap de funcionalidades (%)

**CrewAI**
- O que CrewAI faz melhor?
- Onde SACI EVOLUÍDO vence?
- Overlap de funcionalidades (%)

### 2. PROPOSTA DE VALOR ÚNICA (150 palavras)
- Qual o **ÚNICO** motivo pelo qual alguém escolheria SACI EVOLUÍDO?
- Qual problema ele resolve que os outros não resolvem BEM?
- Exemplo de caso de uso killer (onde SACI é 10x melhor)

### 3. POSICIONAMENTO DE MERCADO (100 palavras)
- SACI EVOLUÍDO é um **produto standalone** ou **feature/biblioteca**?
- Deve competir diretamente com AutoGen/LangGraph ou ser complementar?
- Qual segmento de mercado atacar primeiro? (startups, enterprise, open-source)

## SEJA BRUTAL
Não venda ilusões. Se SACI é 85% overlap com AutoGen, DIGA ISSO.
Identifique os 15% que fazem diferença real.

Responda de forma honesta, analítica e DATA-DRIVEN (quando possível).
"""

ROUND3_PROMPT = """
# RODADA 3: ESTRATÉGIA DE GO-TO-MARKET & IMPACTO

Você é {specialty}.

## CONTEXTO
{context}

## RODADAS ANTERIORES
### Arquitetura (Rodada 1)
{round1}

### Diferenciação (Rodada 2)
{round2}

## SUA MISSÃO
Definir como **lançar SACI EVOLUÍDO** e prever seu **impacto no mercado de AI agents**.

## DELIVERABLES OBRIGATÓRIOS (≈500 palavras)

### 1. ESTRATÉGIA DE LANÇAMENTO (200 palavras)
- **Forma de distribuição:** Open-source? PyPI? GitHub? SaaS?
- **Público inicial:** Quem são os early adopters ideais?
- **Mensagem de marketing:** Como explicar SACI EVOLUÍDO em 1 frase?
- **Canais de divulgação:** Onde promover? (Reddit, HN, Twitter, papers)
- **Timeline:** Roadmap de lançamento (semana 1, mês 1, trimestre 1)

### 2. BARREIRAS DE ADOÇÃO (150 palavras)
- Top 3 motivos pelos quais devs NÃO adotariam SACI EVOLUÍDO
- Como superar cada barreira? (educação, demos, comparações)
- Qual a "tax" de migração de AutoGen/LangGraph para SACI?

### 3. IMPACTO NO MERCADO DE AI (150 palavras)
- **Cenário Otimista:** SACI se torna padrão para debates simples (20% market share)
  - Que mudanças isso causaria no ecossistema?
  - Que reações dos concorrentes (Microsoft, LangChain)?
  
- **Cenário Realista:** SACI é usado por nicho específico (5% market share)
  - Qual nicho?
  - Isso já valeria o esforço?

- **Cenário Pessimista:** SACI não decola (<1% adoção)
  - Por que falhou?
  - Que sinais indicariam essa trajetória?

## FORMATO
Use dados, exemplos concretos, timelines realistas.
Seja pragmático: não prometa revolução se a realidade é evolução incremental.

Responda com VISÃO DE PRODUTO, não só técnica.
"""

# ============================================================================
# FUNÇÃO PRINCIPAL: EXECUTAR DEBATE
# ============================================================================

def consult_agent(agent: dict, prompt: str, round_num: int) -> dict:
    """Consulta um agente específico"""
    
    print("=" * 120)
    print(f"🤖 RODADA {round_num}: {agent['name']}")
    print(f"   Specialty: {agent['specialty']}")
    print("=" * 120)
    
    system_msg = f"You are an expert in {agent['specialty']}. Provide detailed, structured analysis."
    
    print(f"⏳ Enviando prompt (rodada {round_num}) - max_tokens={agent['max_tokens']}...")
    start_time = time.time()
    
    try:
        response = chat(
            model=agent["model"],
            system=system_msg,
            user=prompt,
            temperature=0.3,  # Mais criativo que SACI anterior (era 0.2)
            max_tokens=agent["max_tokens"]
        )
        
        elapsed = time.time() - start_time
        tokens_approx = len(response) // 4
        
        print(f"✓ Resposta recebida! ({elapsed:.1f}s, ~{tokens_approx} tokens)\n")
        
        return {
            "agent": agent["name"],
            "model": agent["model"],
            "specialty": agent["specialty"],
            "response": response,
            "elapsed_seconds": round(elapsed, 1),
            "tokens_approx": tokens_approx,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ ERRO após {elapsed:.1f}s: {type(e).__name__} - {str(e)}\n")
        return {
            "agent": agent["name"],
            "model": agent["model"],
            "specialty": agent["specialty"],
            "response": f"[ERRO: {type(e).__name__} - {str(e)}]",
            "error": str(e),
            "elapsed_seconds": round(elapsed, 1),
            "timestamp": datetime.now().isoformat()
        }


def run_debate():
    """Executa as 3 rodadas do debate"""
    
    print("\n" + "=" * 120)
    print("  DEBATE SACI: ESTRATÉGIA DE PRODUTO - SACI EVOLUÍDO")
    print("  Deliverables: Metodologia + Diferenciação + Go-to-Market")
    print("=" * 120)
    print("\nAgentes participantes:")
    for agent in AGENTS:
        print(f"  • {agent['name']} - {agent['specialty']}")
    print("\n")
    
    # ========================================================================
    # RODADA 1: ARQUITETURA & METODOLOGIA
    # ========================================================================
    
    print("=" * 120)
    print("FASE 1: ARQUITETURA & METODOLOGIA DE IMPLEMENTAÇÃO")
    print("=" * 120 + "\n")
    
    round1_results = []
    
    for agent in AGENTS:
        prompt = ROUND1_PROMPT.format(
            specialty=agent["specialty"],
            context=SACI_EVOLVED_CONTEXT
        )
        
        result = consult_agent(agent, prompt, round_num=1)
        round1_results.append(result)
        
        if agent != AGENTS[-1]:  # Não aguardar após último agente
            print(f"⏸  Aguardando {DELAY_BETWEEN_CALLS}s...\n")
            time.sleep(DELAY_BETWEEN_CALLS)
    
    # Salvar Rodada 1
    round1_file = OUTPUT_DIR / "saci_product_round1_architecture.json"
    with open(round1_file, "w", encoding="utf-8") as f:
        json.dump(round1_results, f, indent=2, ensure_ascii=False)
    
    round1_txt = OUTPUT_DIR / "saci_product_round1_architecture.txt"
    with open(round1_txt, "w", encoding="utf-8") as f:
        for result in round1_results:
            f.write(f"\n{'='*80}\n")
            f.write(f"AGENTE: {result['agent']}\n")
            f.write(f"MODELO: {result['model']}\n")
            f.write(f"{'='*80}\n\n")
            f.write(result['response'])
            f.write("\n\n")
    
    print(f"\n✅ RODADA 1 COMPLETA: {len([r for r in round1_results if 'error' not in r])}/{len(AGENTS)} agentes!\n")
    print(f"  💾 Salvo: {round1_file}")
    print(f"  💾 Salvo (TXT): {round1_txt}\n")
    
    # ========================================================================
    # RODADA 2: ANÁLISE COMPETITIVA
    # ========================================================================
    
    print("\n" + "=" * 120)
    print("FASE 2: ANÁLISE COMPETITIVA & DIFERENCIAÇÃO")
    print("=" * 120 + "\n")
    
    # Preparar contexto da rodada anterior
    previous_context = "\n\n".join([
        f"### {r['agent']} ({r['specialty']})\n{r['response'][:800]}..."
        for r in round1_results if 'error' not in r
    ])
    
    round2_results = []
    
    for agent in AGENTS:
        prompt = ROUND2_PROMPT.format(
            specialty=agent["specialty"],
            context=SACI_EVOLVED_CONTEXT,
            previous_round=previous_context
        )
        
        result = consult_agent(agent, prompt, round_num=2)
        round2_results.append(result)
        
        if agent != AGENTS[-1]:
            print(f"⏸  Aguardando {DELAY_BETWEEN_CALLS}s...\n")
            time.sleep(DELAY_BETWEEN_CALLS)
    
    # Salvar Rodada 2
    round2_file = OUTPUT_DIR / "saci_product_round2_competitive.json"
    with open(round2_file, "w", encoding="utf-8") as f:
        json.dump(round2_results, f, indent=2, ensure_ascii=False)
    
    round2_txt = OUTPUT_DIR / "saci_product_round2_competitive.txt"
    with open(round2_txt, "w", encoding="utf-8") as f:
        for result in round2_results:
            f.write(f"\n{'='*80}\n")
            f.write(f"AGENTE: {result['agent']}\n")
            f.write(f"MODELO: {result['model']}\n")
            f.write(f"{'='*80}\n\n")
            f.write(result['response'])
            f.write("\n\n")
    
    print(f"\n✅ RODADA 2 COMPLETA: {len([r for r in round2_results if 'error' not in r])}/{len(AGENTS)} agentes!\n")
    print(f"  💾 Salvo: {round2_file}")
    print(f"  💾 Salvo (TXT): {round2_txt}\n")
    
    # ========================================================================
    # RODADA 3: GO-TO-MARKET & IMPACTO
    # ========================================================================
    
    print("\n" + "=" * 120)
    print("FASE 3: ESTRATÉGIA DE GO-TO-MARKET & IMPACTO NO MERCADO")
    print("=" * 120 + "\n")
    
    # Preparar contexto das rodadas anteriores
    round1_summary = "\n\n".join([
        f"### {r['agent']}\n{r['response'][:600]}..."
        for r in round1_results if 'error' not in r
    ])
    
    round2_summary = "\n\n".join([
        f"### {r['agent']}\n{r['response'][:600]}..."
        for r in round2_results if 'error' not in r
    ])
    
    round3_results = []
    
    for agent in AGENTS:
        prompt = ROUND3_PROMPT.format(
            specialty=agent["specialty"],
            context=SACI_EVOLVED_CONTEXT,
            round1=round1_summary,
            round2=round2_summary
        )
        
        result = consult_agent(agent, prompt, round_num=3)
        round3_results.append(result)
        
        if agent != AGENTS[-1]:
            print(f"⏸  Aguardando {DELAY_BETWEEN_CALLS}s...\n")
            time.sleep(DELAY_BETWEEN_CALLS)
    
    # Salvar Rodada 3
    round3_file = OUTPUT_DIR / "saci_product_round3_gtm.json"
    with open(round3_file, "w", encoding="utf-8") as f:
        json.dump(round3_results, f, indent=2, ensure_ascii=False)
    
    round3_txt = OUTPUT_DIR / "saci_product_round3_gtm.txt"
    with open(round3_txt, "w", encoding="utf-8") as f:
        for result in round3_results:
            f.write(f"\n{'='*80}\n")
            f.write(f"AGENTE: {result['agent']}\n")
            f.write(f"MODELO: {result['model']}\n")
            f.write(f"{'='*80}\n\n")
            f.write(result['response'])
            f.write("\n\n")
    
    print(f"\n✅ RODADA 3 COMPLETA: {len([r for r in round3_results if 'error' not in r])}/{len(AGENTS)} agentes!")
    print("🎯 ESTRATÉGIA DE PRODUTO COMPLETA!\n")
    print(f"  💾 Salvo: {round3_file}")
    print(f"  💾 Salvo (TXT): {round3_txt}")
    
    # ========================================================================
    # SÍNTESE FINAL & RELATÓRIO EXECUTIVO
    # ========================================================================
    
    synthesis = {
        "debate_metadata": {
            "objective": "Definir estratégia de produto para SACI EVOLUÍDO",
            "deliverables": [
                "Metodologia de implementação detalhada",
                "Análise de diferenciação competitiva",
                "Estratégia de go-to-market e impacto"
            ],
            "date": datetime.now().isoformat(),
            "agents": [{"name": a["name"], "model": a["model"]} for a in AGENTS],
            "total_agents": len(AGENTS),
            "successful_responses_round1": len([r for r in round1_results if 'error' not in r]),
            "successful_responses_round2": len([r for r in round2_results if 'error' not in r]),
            "successful_responses_round3": len([r for r in round3_results if 'error' not in r])
        },
        "round1_architecture": round1_results,
        "round2_competitive": round2_results,
        "round3_gtm": round3_results
    }
    
    synthesis_file = OUTPUT_DIR / "saci_product_FINAL_SYNTHESIS.json"
    with open(synthesis_file, "w", encoding="utf-8") as f:
        json.dump(synthesis, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Síntese completa: {synthesis_file}")
    
    # Gerar relatório executivo em Markdown
    report_file = OUTPUT_DIR / "saci_product_FINAL_REPORT.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# RELATÓRIO FINAL - ESTRATÉGIA DE PRODUTO SACI EVOLUÍDO\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## OBJETIVO\n")
        f.write("Definir estratégia completa para construção e lançamento do SACI EVOLUÍDO:\n")
        f.write("- Metodologia detalhada de implementação (arquitetura, testing, patterns)\n")
        f.write("- Diferenciação competitiva (vs AutoGen, LangGraph, CrewAI)\n")
        f.write("- Go-to-market e impacto no mercado de AI agents\n\n")
        
        f.write("## MODELOS CONSULTADOS\n")
        for agent in AGENTS:
            f.write(f"- {agent['name']}: {agent['specialty']}\n")
        f.write("\n---\n\n")
        
        # Rodada 1
        f.write("## RODADA 1: ARQUITETURA & METODOLOGIA\n\n")
        for result in round1_results:
            if 'error' in result:
                continue
            f.write(f"### {result['agent']}\n\n")
            f.write(result['response'])
            f.write("\n\n")
        
        # Rodada 2
        f.write("\n## RODADA 2: ANÁLISE COMPETITIVA\n\n")
        for result in round2_results:
            if 'error' in result:
                continue
            f.write(f"### {result['agent']}\n\n")
            f.write(result['response'])
            f.write("\n\n")
        
        # Rodada 3
        f.write("\n## RODADA 3: GO-TO-MARKET & IMPACTO\n\n")
        for result in round3_results:
            if 'error' in result:
                continue
            f.write(f"### {result['agent']}\n\n")
            f.write(result['response'])
            f.write("\n\n")
    
    print(f"📄 Relatório executivo: {report_file}")
    
    print("\n" + "=" * 120)
    print("DEBATE SACI CONCLUÍDO!")
    print("=" * 120)
    
    return synthesis


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Verificar API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ ERRO: OPENROUTER_API_KEY não encontrada!")
        print("   Configure: $env:OPENROUTER_API_KEY = '...'")
        sys.exit(1)
    
    print("[OK] API Key carregada")
    
    try:
        synthesis = run_debate()
        print("\n✅ Debate concluído com sucesso!")
        print(f"✅ {synthesis['debate_metadata']['successful_responses_round1']}/{len(AGENTS)} agentes na Rodada 1")
        print(f"✅ {synthesis['debate_metadata']['successful_responses_round2']}/{len(AGENTS)} agentes na Rodada 2")
        print(f"✅ {synthesis['debate_metadata']['successful_responses_round3']}/{len(AGENTS)} agentes na Rodada 3")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Debate interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERRO FATAL: {type(e).__name__}")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
