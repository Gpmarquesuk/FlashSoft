"""
CONSULTA SACI - EVOLUÇÃO DA IMPLEMENTAÇÃO ATUAL
Objetivo: Como incorporar as melhores características da SACI ideal na implementação 
         simplificada atual (sem LangGraph, sem AutoGen)?

RODADA 1: Propostas de Features/Melhorias
RODADA 2: Análise de Pros/Contras vs. Implementação Ideal
RODADA 3: Roadmap de Implementação Incremental

CONTEXTO:
- Implementação atual: Script Python direto (~700 linhas), 3 rodadas fixas, convergência qualitativa
- SACI Ideal (consenso dos 4 modelos): LangGraph + AutoGen + Custom Layer (~300 linhas)
  * Métricas quantitativas: semântica (0.4) + voting (0.35) + critique (0.25)
  * Threshold ≥75%, max 5 rounds, early stopping
  
DESAFIO: Adicionar as melhores features da SACI ideal mantendo simplicidade (sem frameworks pesados)
"""

import os
import sys
import json
import time
from datetime import datetime
from llm_client import chat

# Carregar API key
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise RuntimeError("OPENROUTER_API_KEY não encontrada!")

print("[OK] API Key carregada")

# 4 especialistas
AGENTS = {
    'claude_sonnet': {
        'id': 'anthropic/claude-sonnet-4.5',
        'name': 'Claude Sonnet 4.5',
        'specialty': 'Arquitetura de sistemas, trade-offs técnicos'
    },
    'gpt5_codex': {
        'id': 'openai/gpt-5-codex',
        'name': 'GPT-5 Codex',
        'specialty': 'Implementação prática, código limpo e manutenível'
    },
    'gemini': {
        'id': 'google/gemini-2.5-pro',
        'name': 'Gemini 2.5 PRO',
        'specialty': 'Análise de viabilidade, ROI de features'
    },
    'grok': {
        'id': 'x-ai/grok-4',
        'name': 'Grok 4',
        'specialty': 'Pragmatismo, soluções incrementais'
    }
}

# Contexto da implementação atual
CONTEXT_CURRENT = """
IMPLEMENTAÇÃO ATUAL (FUNCIONANDO):
- Script Python direto: saci_implementation_strategy.py (~700 linhas)
- 3 rodadas fixas: Propostas → Críticas → Convergência
- Convergência qualitativa: LLMs sintetizam consenso via prompt engineering
- Sem frameworks pesados: apenas llm_client.py + chat()
- 100% funcional: acabou de rodar com sucesso (4/4 modelos responderam)

VANTAGENS ATUAIS:
✓ Simplicidade: fácil de entender e modificar
✓ Sem dependências pesadas: apenas OpenAI SDK
✓ Flexibilidade: prompts facilmente ajustáveis
✓ Interpretabilidade: humanos leem e validam o consenso

LIMITAÇÕES ATUAIS:
✗ Convergência subjetiva: depende da qualidade da síntese do LLM
✗ Rodadas fixas: sempre 3, pode ser insuficiente ou excessivo
✗ Sem métricas objetivas: difícil saber "quanto" de consenso há
✗ Sem rastreabilidade quantitativa: apenas textos longos
✗ Não escala bem: com 10+ agentes, fica difícil interpretar
"""

# Contexto da SACI ideal
CONTEXT_IDEAL = """
SACI IDEAL (CONSENSO DOS 4 TOP MODELS):
- LangGraph + AutoGen + Custom Layer (~300 linhas)
- Métricas quantitativas multi-dimensionais:
  * Semântica: embeddings + similaridade cosseno (peso 0.4)
  * Voting: extração de votos explícitos (peso 0.35)
  * Critique: validação de críticas endereçadas (peso 0.25)
- Threshold: ≥75% para convergência
- Max 5 rounds com early stopping
- Rastreabilidade: logs estruturados com scores por rodada

VANTAGENS DA SACI IDEAL:
✓ Convergência objetiva: score numérico 0-1
✓ Detecção de falso consenso: critique penaliza acordos superficiais
✓ Adaptabilidade: early stopping economiza custos
✓ Rastreabilidade: métricas por rodada em JSON
✓ Escalabilidade: processa 10, 20, 100 agentes

DESVANTAGENS DA SACI IDEAL:
✗ Complexidade: 2000+ linhas de código
✗ Dependências pesadas: LangGraph, AutoGen, sentence-transformers
✗ 3 semanas de desenvolvimento
✗ Over-engineering: métricas podem ser enganosas
✗ Perda de interpretabilidade: confia em números, não em textos
"""

# RODADA 1: Propostas de Features/Melhorias
PROMPT_ROUND1 = f"""{CONTEXT_CURRENT}

{CONTEXT_IDEAL}

# RODADA 1: PROPOSTAS DE FEATURES/MELHORIAS

Você é um especialista em {'{specialty}'}.

**DESAFIO:** Como evoluir a implementação atual (script Python simples) para incorporar as 
melhores características da SACI ideal, MAS sem usar LangGraph nem AutoGen?

## SUAS PROPOSTAS DEVEM INCLUIR:

### 1. TOP 3 FEATURES A ADICIONAR (150 palavras)
Escolha as 3 features mais valiosas da SACI ideal que podem ser implementadas de forma 
simplificada. Para cada uma:
- Nome da feature
- Benefício específico
- Complexidade estimada (Baixa/Média/Alta)
- Dependências necessárias (se houver)

### 2. ARQUITETURA SIMPLIFICADA (200 palavras)
Como estruturar o código para adicionar essas features mantendo simplicidade?
- Novos módulos/classes (se necessário)
- Onde se encaixam no fluxo atual (Rodadas 1→2→3)
- Como evitar over-engineering

### 3. MÉTRICAS QUANTITATIVAS VIÁVEIS (150 palavras)
Quais métricas da SACI ideal (semântica, voting, critique) podem ser implementadas 
sem LangGraph/AutoGen? Como computá-las de forma leve?

### 4. IMPLEMENTAÇÃO INCREMENTAL (100 palavras)
Ordem de prioridade para adicionar features:
- Fase 1 (1 dia): [feature mais simples e valiosa]
- Fase 2 (2-3 dias): [segunda feature]
- Fase 3 (1 semana): [terceira feature, se valer a pena]

### 5. O QUE NÃO FAZER (100 palavras)
Quais features da SACI ideal DEFINITIVAMENTE não valem a pena adicionar 
(complexidade >> benefício)?

**RESTRIÇÕES:**
- SEM LangGraph
- SEM AutoGen
- Máximo 300 linhas de código adicional
- Deve rodar em Windows/PowerShell
- Compatível com llm_client.py existente

Max 700 palavras.
"""

# RODADA 2: Análise de Pros/Contras
def build_critique_prompt(all_proposals: dict) -> str:
    proposals_text = "\n\n".join([
        f"{'='*80}\n"
        f"PROPOSTA DE {data['agent_name'].upper()}:\n"
        f"{'='*80}\n"
        f"{data['response']}"
        for key, data in all_proposals.items()
    ])
    
    return f"""{CONTEXT_CURRENT}

{CONTEXT_IDEAL}

# RODADA 2: ANÁLISE DE PROS/CONTRAS

Você viu as 4 propostas de evolução da SACI:

{proposals_text}

## SUA TAREFA: ANÁLISE CRÍTICA COMPARATIVA

Para CADA proposta dos outros 3 agentes, analise:

### 1. PROS vs. IMPLEMENTAÇÃO ATUAL
- Que problemas reais da implementação atual essa proposta resolve?
- O ganho de funcionalidade justifica a complexidade adicional?
- Exemplos concretos de casos de uso beneficiados

### 2. PROS vs. SACI IDEAL
- Como essa proposta se compara com a SACI ideal (com LangGraph/AutoGen)?
- Que % dos benefícios da SACI ideal é capturado?
- O que se perde ao não usar frameworks pesados?

### 3. CONTRAS E RISCOS
- Over-engineering: a proposta adiciona complexidade desnecessária?
- Manutenibilidade: código fica mais difícil de entender?
- Dependências: novas bibliotecas introduzem fragilidade?
- Falsos positivos: métricas quantitativas podem enganar?

### 4. VIABILIDADE DE IMPLEMENTAÇÃO
- As 300 linhas de código são suficientes? Realista?
- O roadmap incremental (1 dia → 3 dias → 1 semana) é factível?
- Há riscos de "scope creep" (começar simples, terminar complexo)?

## FORMATO

```
ANÁLISE DA PROPOSTA [NOME DO AGENTE]:

PROS vs. ATUAL:
- [benefícios concretos]

PROS vs. IDEAL:
- Captura ~X% dos benefícios
- Perde: [o que não consegue fazer]

CONTRAS:
- [riscos de complexidade]
- [riscos de manutenção]

VIABILIDADE: [Realista | Otimista | Inviável]

RECOMENDAÇÃO: [Implementar tudo | Implementar parcialmente | Descartar]
```

Repita para cada proposta.

Máximo: 800 palavras.
"""

# RODADA 3: Roadmap de Implementação Incremental
def build_convergence_prompt(proposals: dict, critiques: dict) -> str:
    return f"""{CONTEXT_CURRENT}

{CONTEXT_IDEAL}

# RODADA 3: ROADMAP CONSENSUAL DE IMPLEMENTAÇÃO

Baseado nas 4 propostas e críticas, defina um **PLANO DE AÇÃO CONSENSUAL**.

## PARTE 1: FEATURES CONSENSUAIS

Liste as features que pelo menos 3 dos 4 agentes concordaram em adicionar:

### Feature 1: [Nome]
- **O que é:** [descrição em 1 frase]
- **Benefício:** [por que adicionar?]
- **Complexidade:** [Baixa/Média/Alta]
- **Linhas de código:** [~X linhas]
- **Dependências:** [bibliotecas necessárias, ou "nenhuma"]

[Repita para Feature 2, Feature 3, etc.]

## PARTE 2: ROADMAP INCREMENTAL DETALHADO

### FASE 1 (1 dia - Feature mais valiosa e simples)
- **Feature a implementar:** [nome]
- **Onde adicionar no código atual:**
  ```python
  # Em saci_implementation_strategy.py, após a Rodada 3:
  def calculate_[feature_name](round3_results):
      # ~50 linhas
      pass
  ```
- **Como testar:** [critério de sucesso]
- **Risco:** [o que pode dar errado?]

### FASE 2 (2-3 dias - Segunda feature)
- **Feature a implementar:** [nome]
- **Integração com Fase 1:** [como as features interagem?]
- **Onde adicionar:**
  ```python
  # Novo módulo: convergence_metrics.py (~150 linhas)
  class ConvergenceAnalyzer:
      def __init__(self):
          pass
  ```
- **Como testar:** [critério de sucesso]
- **Risco:** [o que pode dar errado?]

### FASE 3 (1 semana - Terceira feature, SE valer a pena)
- **Feature a implementar:** [nome]
- **Justificativa:** [por que adicionar depois das duas primeiras?]
- **Onde adicionar:** [estrutura]
- **Como testar:** [critério de sucesso]
- **Risco:** [o que pode dar errar?]

## PARTE 3: O QUE NÃO FAZER (CONSENSO)

Liste features da SACI ideal que os agentes concordaram em **NÃO implementar**:

1. **[Feature X]**: Motivo: [complexidade >> benefício]
2. **[Feature Y]**: Motivo: [dependência pesada demais]
3. **[Feature Z]**: Motivo: [não resolve problema real da implementação atual]

## PARTE 4: COMPARAÇÃO FINAL

### Implementação Atual (Antes)
- Linhas de código: 700
- Dependências: OpenAI SDK
- Convergência: Qualitativa (prompt-based)
- Rastreabilidade: Textos em JSON

### Implementação Evoluída (Depois - Fases 1+2+3)
- Linhas de código: ~700 + 300 = 1000
- Dependências: [listar novas]
- Convergência: [Qualitativa + X métricas quantitativas]
- Rastreabilidade: [textos + scores numéricos]

### vs. SACI Ideal (LangGraph + AutoGen)
- **Captura X% dos benefícios** com Y% da complexidade
- **Perde:** [o que não consegue fazer sem frameworks]
- **Ganha:** [o que ganha com simplicidade]

## PARTE 5: DECISÃO FINAL

**RECOMENDAÇÃO CONSENSUAL:**

- [ ] Implementar TODAS as 3 fases (vale a pena)
- [ ] Implementar apenas Fases 1+2 (Fase 3 é over-engineering)
- [ ] Implementar apenas Fase 1 (resto não compensa)
- [ ] NÃO implementar nada (implementação atual já é ótima)

**Justificativa:** [2-3 frases explicando a decisão]

**Confiança:** [0-100%]

Máximo: 1000 palavras.
"""

def consult_agent(agent_key: str, agent_info: dict, prompt: str, round_num: int, max_retries: int = 3) -> tuple:
    """Consulta um agente com retry"""
    agent_id = agent_info['id']
    agent_name = agent_info['name']
    specialty = agent_info['specialty']
    
    print(f"\n{'='*80}")
    print(f"🤖 RODADA {round_num}: {agent_name}")
    print(f"   Specialty: {specialty}")
    print(f"{'='*80}\n")
    
    # Substituir placeholder {specialty} no prompt
    final_prompt = prompt.replace('{specialty}', specialty)
    
    system_prompt = f"""You are {agent_name}, a specialist in {specialty}.
You are participating in a SACI debate about evolving the current simple implementation 
to incorporate best features from the ideal SACI (but WITHOUT LangGraph/AutoGen).
Be practical, pragmatic, and focus on real benefits vs. complexity trade-offs."""
    
    max_tokens_map = {
        'anthropic/claude-sonnet-4.5': 8192,
        'openai/gpt-5-codex': 4096,
        'google/gemini-2.5-pro': 8192,
        'x-ai/grok-4': 8192
    }
    
    max_tokens = max_tokens_map.get(agent_id, 4096)
    
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                print(f"⚠️  RETRY {attempt}/{max_retries} para {agent_name}...")
                time.sleep(5 * attempt)
            else:
                print(f"⏳ Enviando prompt (rodada {round_num}) - max_tokens={max_tokens}...")
            
            start_time = time.time()
            
            response = chat(
                model=agent_id,
                system=system_prompt,
                user=final_prompt,
                max_tokens=max_tokens,
                temperature=0.2
            )
            
            elapsed = time.time() - start_time
            
            if not response or len(response.strip()) < 100:
                raise ValueError(f"Resposta muito curta: {len(response)} chars")
            
            input_tokens = (len(system_prompt) + len(final_prompt)) // 4
            output_tokens = len(response) // 4
            
            print(f"✓ Resposta recebida! ({elapsed:.1f}s, ~{output_tokens} tokens)")
            
            return True, response, elapsed, input_tokens, output_tokens
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ ERRO (tentativa {attempt}/{max_retries}):")
            print(f"   Tipo: {type(e).__name__}")
            print(f"   Mensagem: {str(e)}")
            
            if attempt == max_retries:
                print(f"\n🚨 FALHA CRÍTICA: {agent_name} não respondeu!")
                return False, f"FALHA: {e}", 0, 0, 0
            
            continue
    
    return False, "ERRO DESCONHECIDO", 0, 0, 0

def save_results(round_num: int, results: dict, filename_prefix: str):
    """Salva resultados de uma rodada"""
    filename = f"logs/saci_evolution_round{round_num}_{filename_prefix}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"  💾 Salvo: {filename}")
    
    txt_filename = filename.replace('.json', '.txt')
    with open(txt_filename, 'w', encoding='utf-8') as f:
        for agent_key, data in results.items():
            f.write(f"\n{'='*80}\n")
            f.write(f"{data['agent_name']}\n")
            f.write(f"{'='*80}\n\n")
            f.write(data['response'])
            f.write(f"\n\n")
    
    print(f"  💾 Salvo (TXT): {txt_filename}")

def main():
    print("\n" + "="*80)
    print("CONSULTA SACI - EVOLUÇÃO DA IMPLEMENTAÇÃO ATUAL")
    print("Objetivo: Melhores features da SACI ideal SEM LangGraph/AutoGen")
    print("="*80 + "\n")
    
    print("Agentes participantes:")
    for key, info in AGENTS.items():
        print(f"  • {info['name']} - {info['specialty']}")
    print("\n")
    
    # ============================================================
    # RODADA 1: PROPOSTAS DE FEATURES
    # ============================================================
    print("\n" + "="*80)
    print("FASE 1: PROPOSTAS DE FEATURES/MELHORIAS")
    print("="*80 + "\n")
    
    round1_results = {}
    
    for agent_key, agent_info in AGENTS.items():
        success, response, elapsed, in_tokens, out_tokens = consult_agent(
            agent_key, agent_info, PROMPT_ROUND1, round_num=1, max_retries=3
        )
        
        round1_results[agent_key] = {
            'agent_name': agent_info['name'],
            'success': success,
            'response': response,
            'elapsed': elapsed,
            'tokens': {'input': in_tokens, 'output': out_tokens}
        }
        
        if agent_key != list(AGENTS.keys())[-1]:
            print("\n⏸  Aguardando 5s...")
            time.sleep(5)
    
    successful = sum(1 for r in round1_results.values() if r['success'])
    if successful < 4:
        print(f"\n🚨 RODADA 1 INCOMPLETA: {successful}/4 agentes. Abortando...")
        return
    
    print(f"\n✅ RODADA 1 COMPLETA: {successful}/4 agentes!\n")
    save_results(1, round1_results, "proposals")
    
    # ============================================================
    # RODADA 2: ANÁLISE DE PROS/CONTRAS
    # ============================================================
    print("\n\n" + "="*80)
    print("FASE 2: ANÁLISE DE PROS/CONTRAS")
    print("="*80 + "\n")
    
    critique_prompt = build_critique_prompt(round1_results)
    round2_results = {}
    
    for agent_key, agent_info in AGENTS.items():
        success, response, elapsed, in_tokens, out_tokens = consult_agent(
            agent_key, agent_info, critique_prompt, round_num=2, max_retries=3
        )
        
        round2_results[agent_key] = {
            'agent_name': agent_info['name'],
            'success': success,
            'response': response,
            'elapsed': elapsed,
            'tokens': {'input': in_tokens, 'output': out_tokens}
        }
        
        if agent_key != list(AGENTS.keys())[-1]:
            print("\n⏸  Aguardando 5s...")
            time.sleep(5)
    
    successful = sum(1 for r in round2_results.values() if r['success'])
    if successful < 4:
        print(f"\n🚨 RODADA 2 INCOMPLETA: {successful}/4 agentes. Abortando...")
        return
    
    print(f"\n✅ RODADA 2 COMPLETA: {successful}/4 agentes!\n")
    save_results(2, round2_results, "analysis")
    
    # ============================================================
    # RODADA 3: ROADMAP CONSENSUAL
    # ============================================================
    print("\n\n" + "="*80)
    print("FASE 3: ROADMAP CONSENSUAL DE IMPLEMENTAÇÃO")
    print("="*80 + "\n")
    
    convergence_prompt = build_convergence_prompt(round1_results, round2_results)
    round3_results = {}
    
    for agent_key, agent_info in AGENTS.items():
        success, response, elapsed, in_tokens, out_tokens = consult_agent(
            agent_key, agent_info, convergence_prompt, round_num=3, max_retries=3
        )
        
        round3_results[agent_key] = {
            'agent_name': agent_info['name'],
            'success': success,
            'response': response,
            'elapsed': elapsed,
            'tokens': {'input': in_tokens, 'output': out_tokens}
        }
        
        if agent_key != list(AGENTS.keys())[-1]:
            print("\n⏸  Aguardando 5s...")
            time.sleep(5)
    
    successful = sum(1 for r in round3_results.values() if r['success'])
    if successful < 4:
        print(f"\n🚨 RODADA 3 INCOMPLETA: {successful}/4 agentes. Abortando...")
        return
    
    print(f"\n✅ RODADA 3 COMPLETA: {successful}/4 agentes!")
    print("🎯 ROADMAP CONSENSUAL PRONTO!\n")
    
    save_results(3, round3_results, "roadmap")
    
    # ============================================================
    # SÍNTESE FINAL
    # ============================================================
    synthesis = {
        'timestamp': datetime.now().isoformat(),
        'agents': list(AGENTS.keys()),
        'round1_proposals': round1_results,
        'round2_analysis': round2_results,
        'round3_roadmap': round3_results
    }
    
    with open('logs/saci_evolution_FINAL_SYNTHESIS.json', 'w', encoding='utf-8') as f:
        json.dump(synthesis, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Síntese completa: logs/saci_evolution_FINAL_SYNTHESIS.json")
    
    # Criar relatório executivo
    report = f"""# RELATÓRIO FINAL - EVOLUÇÃO DA SACI
Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## OBJETIVO
Incorporar melhores características da SACI ideal (LangGraph + AutoGen) 
na implementação atual simples, MAS sem usar frameworks pesados.

## MODELOS CONSULTADOS
- {AGENTS['claude_sonnet']['name']}: {AGENTS['claude_sonnet']['specialty']}
- {AGENTS['gpt5_codex']['name']}: {AGENTS['gpt5_codex']['specialty']}
- {AGENTS['gemini']['name']}: {AGENTS['gemini']['specialty']}
- {AGENTS['grok']['name']}: {AGENTS['grok']['specialty']}

---

## RODADA 1: PROPOSTAS DE FEATURES

"""
    
    for agent_key, data in round1_results.items():
        if data['success']:
            report += f"### {data['agent_name']}\n\n"
            report += f"{data['response'][:1500]}...\n\n"
    
    report += "\n## RODADA 2: ANÁLISE DE PROS/CONTRAS\n\n"
    
    for agent_key, data in round2_results.items():
        if data['success']:
            report += f"### {data['agent_name']}\n\n"
            report += f"{data['response'][:1500]}...\n\n"
    
    report += "\n## RODADA 3: ROADMAP CONSENSUAL\n\n"
    
    for agent_key, data in round3_results.items():
        if data['success']:
            report += f"### {data['agent_name']}\n\n"
            report += f"{data['response']}\n\n"
    
    with open('logs/saci_evolution_FINAL_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Relatório executivo: logs/saci_evolution_FINAL_REPORT.md")
    print("\n" + "="*80)
    print("DEBATE SACI CONCLUÍDO!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
