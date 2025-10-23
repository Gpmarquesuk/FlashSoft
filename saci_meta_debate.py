"""
CONSULTA SACI META-RECURSIVA
Tema: Usar metodologia SACI para validar/criar a própria SACI

RODADA 1: Initial Proposals
RODADA 2: Critiques
RODADA 3: Convergence + Market Analysis

OBJETIVOS:
1. Validar se SACI é realmente necessária (vs usar ferramenta pronta)
2. Comparar SACI com Devin, AutoGen, LangGraph, CrewAI, etc
3. Decidir: BUILD (implementar SACI) ou BUY (usar ferramenta existente)
"""

import os
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

print(f"✓ API Key carregada")

# 4 especialistas da SACI
AGENTS = {
    'claude': {
        'id': 'anthropic/claude-sonnet-4.5',
        'name': 'Claude 3.5 Sonnet',
        'specialty': 'Arquitetura de sistemas, crítica construtiva'
    },
    'gpt4o': {
        'id': 'openai/gpt-4o',
        'name': 'GPT-4o',
        'specialty': 'Análise balanceada, sintetização'
    },
    'gemini': {
        'id': 'google/gemini-2.5-pro',
        'name': 'Gemini 2.5 PRO',
        'specialty': 'Visão técnica, benchmarking'
    },
    'grok': {
        'id': 'x-ai/grok-4',
        'name': 'Grok 4',
        'specialty': 'Perspectiva alternativa, pragmatismo'
    }
}

# Contexto da consulta anterior
CONTEXT_PREVIOUS = """
CONTEXTO - CONSULTA ANTERIOR SOBRE SACI:

4 especialistas (Gemini, GPT-5 Codex, Grok 4, Claude 3.5) propuseram SACI como:
- Sistema de debate entre 4 IAs com convergência forçada
- 5 rodadas: Initial Proposal → Critique → Refinement → Convergence → Vote
- Detecção multi-métrica (similaridade semântica, votos, críticas) >= 75%
- Stack: Pydantic v2 + asyncio + sentence-transformers
- Modelos: Claude 3.5, GPT-4o, Gemini 2.5 Pro, Grok 4

ESPECIFICAÇÃO CRIADA: SACI_SPEC.md (937 linhas)
"""

# RODADA 1: Initial Proposals
PROMPT_ROUND1 = f"""{CONTEXT_PREVIOUS}

# RODADA 1: INITIAL PROPOSAL

## CONTEXTO META
Você está participando de um debate SACI sobre a própria SACI. Irônico, não?

## SUA TAREFA
Analise criticamente a proposta SACI e responda:

### PARTE A: Validação do Conceito SACI
1. **A SACI é realmente inovadora** ou apenas reempacota conceitos conhecidos?
2. **Qual o valor único** que SACI oferece vs sistemas multi-agente existentes?
3. **Os 5 rounds são necessários** ou é over-engineering?

### PARTE B: Análise Competitiva (CRÍTICO!)
Compare SACI com ferramentas PRONTAS no mercado:

#### vs **Devin** (Cognition Labs)
- Similaridades e diferenças
- Devin resolve os mesmos problemas?
- Vale criar SACI quando Devin existe?

#### vs **AutoGen** (Microsoft)
- AutoGen já faz debate multi-agente?
- Como SACI difere de AutoGen's GroupChat?
- Podemos usar AutoGen em vez de criar SACI?

#### vs **LangGraph** (LangChain)
- LangGraph já orquestra agentes com grafos
- SACI adiciona algo que LangGraph não tem?
- LangGraph resolve nosso problema?

#### vs **CrewAI**
- CrewAI já faz agentes colaborativos
- Como SACI se compara?
- Vale a pena reinventar a roda?

#### vs **Outras** (AgentGPT, SuperAGI, etc)
- Há outras ferramentas que já fazem convergência?
- O que SACI oferece que elas não têm?

### PARTE C: Decisão BUILD vs BUY
**RESPONDA DIRETAMENTE:**
- **BUILD:** Implementar SACI do zero (justifique por quê vale o esforço)
- **BUY:** Usar ferramenta pronta (qual? por quê?)
- **HYBRID:** Usar framework + customizar (como?)

**SEJA BRUTALMENTE HONESTO.** Se SACI é desnecessária, diga!

## FORMATO DE RESPOSTA
```
PROPOSTA: [BUILD | BUY | HYBRID]

JUSTIFICATIVA:
[Sua análise técnica detalhada]

FERRAMENTA RECOMENDADA (se BUY/HYBRID):
[Nome da ferramenta]

CONFIANÇA: [0-100%]
```

Máximo: 1500 tokens.
"""

# RODADA 2: Critiques
def build_critique_prompt(all_proposals: dict) -> str:
    proposals_text = "\n\n".join([
        f"{'='*80}\n"
        f"PROPOSTA DE {data['agent_name'].upper()}:\n"
        f"{'='*80}\n"
        f"{data['response']}"
        for key, data in all_proposals.items()
    ])
    
    return f"""{CONTEXT_PREVIOUS}

# RODADA 2: CRITIQUE

Você acabou de ver as propostas dos outros 3 especialistas:

{proposals_text}

## SUA TAREFA
Para CADA proposta dos outros (exceto a sua), forneça:

1. **PONTOS FORTES** (o que concordo)
2. **PONTOS FRACOS** (o que discordo ou falta)
3. **GAPS NA ANÁLISE** (o que não foi considerado)
4. **SUGESTÕES** (como melhorar a proposta)

**SEJA ESPECÍFICO.** Critique argumentos técnicos, não apenas "concordo".

Formato:
```
CRÍTICA À PROPOSTA [NOME DO AGENTE]:

PONTOS FORTES:
- [específico]

PONTOS FRACOS:
- [específico]

GAPS:
- [o que faltou analisar]

SUGESTÕES:
- [como melhorar]

SEVERIDADE: [minor | moderate | critical]
```

Repita para cada proposta dos outros 3.

Máximo: 2000 tokens.
"""

# RODADA 3: Convergence
def build_convergence_prompt(proposals: dict, critiques: dict) -> str:
    all_content = f"""
RODADA 1 - PROPOSTAS:
{json.dumps({k: v['response'][:500] + '...' for k, v in proposals.items()}, indent=2, ensure_ascii=False)}

RODADA 2 - CRÍTICAS:
{json.dumps({k: v['response'][:500] + '...' for k, v in critiques.items()}, indent=2, ensure_ascii=False)}
"""
    
    return f"""{CONTEXT_PREVIOUS}

# RODADA 3: CONVERGÊNCIA FINAL

Você viu as 4 propostas iniciais e as críticas cruzadas.

{all_content}

## TAREFA DE CONVERGÊNCIA

Sintetize uma DECISÃO FINAL consensual:

1. **CONSENSO IDENTIFICADO:**
   - Quantos propuseram BUILD? BUY? HYBRID?
   - Quais ferramentas foram mais mencionadas?
   - Há convergência clara ou divergência?

2. **ANÁLISE COMPETITIVA CONSOLIDADA:**
   - Qual ferramenta existente é MAIS similar à SACI?
   - Essa ferramenta resolve 80%+ do problema?
   - Se sim, qual o GAP que SACI preencheria?

3. **DECISÃO FINAL (MAJORITÁRIA):**
   ```
   DECISÃO: [BUILD | BUY | HYBRID]
   
   FERRAMENTA (se BUY/HYBRID): [nome específico]
   
   JUSTIFICATIVA CONSOLIDADA:
   [Sintetize os MELHORES argumentos das 4 propostas]
   
   PLANO DE AÇÃO IMEDIATO:
   [Próximos passos concretos]
   
   CONSENSO: [X de 4 agentes concordam]
   ```

4. **VOTO FINAL:**
   Você APROVA a decisão majoritária?
   - [ ] SIM, concordo totalmente
   - [ ] SIM, com ressalvas (quais?)
   - [ ] NÃO, discordo (por quê?)

Máximo: 1500 tokens.
"""

def consult_agent(agent_key: str, agent_info: dict, prompt: str, round_num: int) -> tuple:
    """Consulta um agente em uma rodada específica"""
    agent_id = agent_info['id']
    agent_name = agent_info['name']
    
    print(f"\n{'='*80}")
    print(f"🤖 RODADA {round_num}: {agent_name}")
    print(f"   Model ID: {agent_id}")
    print(f"   Specialty: {agent_info['specialty']}")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    system_prompt = f"""You are {agent_name}, a specialist in {agent_info['specialty']}.
You are participating in a SACI-style debate about whether SACI itself should be built.
Be technical, honest, and pragmatic. If existing tools suffice, say so clearly."""
    
    try:
        print(f"⏳ Enviando prompt (rodada {round_num})...")
        
        response = chat(
            model=agent_id,
            system=system_prompt,
            user=prompt,
            max_tokens=2000 if round_num == 2 else 1500,
            temperature=0.3
        )
        
        elapsed = time.time() - start_time
        
        input_tokens = (len(system_prompt) + len(prompt)) // 4
        output_tokens = len(response) // 4
        
        print(f"✓ Resposta recebida! ({elapsed:.1f}s, ~{output_tokens} tokens)")
        
        return True, response, elapsed, input_tokens, output_tokens
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False, str(e), 0, 0, 0

def save_results(round_num: int, results: dict, filename_prefix: str):
    """Salva resultados de uma rodada"""
    filename = f"logs/saci_meta_round{round_num}_{filename_prefix}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"  💾 Salvo: {filename}")

def main():
    print("\n" + "="*80)
    print("CONSULTA SACI META-RECURSIVA")
    print("Usando metodologia SACI para validar/criar a própria SACI")
    print("="*80 + "\n")
    
    print("Agentes participantes:")
    for key, info in AGENTS.items():
        print(f"  • {info['name']} - {info['specialty']}")
    print("\n")
    
    # ============================================================
    # RODADA 1: INITIAL PROPOSALS
    # ============================================================
    print("\n" + "="*80)
    print("FASE 1: INITIAL PROPOSALS (BUILD vs BUY)")
    print("="*80 + "\n")
    
    round1_results = {}
    
    for agent_key, agent_info in AGENTS.items():
        success, response, elapsed, in_tokens, out_tokens = consult_agent(
            agent_key, agent_info, PROMPT_ROUND1, round_num=1
        )
        
        round1_results[agent_key] = {
            'agent_name': agent_info['name'],
            'success': success,
            'response': response,
            'elapsed': elapsed,
            'tokens': {'input': in_tokens, 'output': out_tokens}
        }
        
        if agent_key != list(AGENTS.keys())[-1]:
            print("\n⏸  Aguardando 3s...")
            time.sleep(3)
    
    save_results(1, round1_results, "proposals")
    
    # ============================================================
    # RODADA 2: CRITIQUES
    # ============================================================
    print("\n\n" + "="*80)
    print("FASE 2: CRITIQUES (Agentes criticam uns aos outros)")
    print("="*80 + "\n")
    
    critique_prompt = build_critique_prompt(round1_results)
    round2_results = {}
    
    for agent_key, agent_info in AGENTS.items():
        success, response, elapsed, in_tokens, out_tokens = consult_agent(
            agent_key, agent_info, critique_prompt, round_num=2
        )
        
        round2_results[agent_key] = {
            'agent_name': agent_info['name'],
            'success': success,
            'response': response,
            'elapsed': elapsed,
            'tokens': {'input': in_tokens, 'output': out_tokens}
        }
        
        if agent_key != list(AGENTS.keys())[-1]:
            print("\n⏸  Aguardando 3s...")
            time.sleep(3)
    
    save_results(2, round2_results, "critiques")
    
    # ============================================================
    # RODADA 3: CONVERGENCE
    # ============================================================
    print("\n\n" + "="*80)
    print("FASE 3: CONVERGENCE (Decisão final consensual)")
    print("="*80 + "\n")
    
    convergence_prompt = build_convergence_prompt(round1_results, round2_results)
    round3_results = {}
    
    for agent_key, agent_info in AGENTS.items():
        success, response, elapsed, in_tokens, out_tokens = consult_agent(
            agent_key, agent_info, convergence_prompt, round_num=3
        )
        
        round3_results[agent_key] = {
            'agent_name': agent_info['name'],
            'success': success,
            'response': response,
            'elapsed': elapsed,
            'tokens': {'input': in_tokens, 'output': out_tokens}
        }
        
        if agent_key != list(AGENTS.keys())[-1]:
            print("\n⏸  Aguardando 3s...")
            time.sleep(3)
    
    save_results(3, round3_results, "convergence")
    
    # ============================================================
    # SÍNTESE FINAL
    # ============================================================
    print("\n\n" + "="*80)
    print("SÍNTESE FINAL DO DEBATE SACI")
    print("="*80 + "\n")
    
    # Análise de votos
    build_votes = 0
    buy_votes = 0
    hybrid_votes = 0
    
    for agent_key, data in round3_results.items():
        if data['success']:
            response_lower = data['response'].lower()
            if 'decisão: build' in response_lower or 'decisao: build' in response_lower:
                build_votes += 1
                print(f"  {data['agent_name']}: BUILD")
            elif 'decisão: buy' in response_lower or 'decisao: buy' in response_lower:
                buy_votes += 1
                print(f"  {data['agent_name']}: BUY")
            elif 'decisão: hybrid' in response_lower or 'decisao: hybrid' in response_lower:
                hybrid_votes += 1
                print(f"  {data['agent_name']}: HYBRID")
    
    print(f"\n📊 RESULTADO DA VOTAÇÃO:")
    print(f"  BUILD: {build_votes}/4")
    print(f"  BUY: {buy_votes}/4")
    print(f"  HYBRID: {hybrid_votes}/4")
    
    if max(build_votes, buy_votes, hybrid_votes) >= 3:
        decision = 'BUILD' if build_votes >= 3 else ('BUY' if buy_votes >= 3 else 'HYBRID')
        print(f"\n✅ CONSENSO ALCANÇADO: {decision}")
    else:
        print(f"\n⚠️  SEM CONSENSO CLARO (maioria não atingida)")
    
    # Salvar síntese
    synthesis = {
        'timestamp': datetime.now().isoformat(),
        'votes': {
            'build': build_votes,
            'buy': buy_votes,
            'hybrid': hybrid_votes
        },
        'consensus': decision if max(build_votes, buy_votes, hybrid_votes) >= 3 else 'NO_CONSENSUS',
        'round1_proposals': round1_results,
        'round2_critiques': round2_results,
        'round3_convergence': round3_results
    }
    
    with open('logs/saci_meta_FINAL_SYNTHESIS.json', 'w', encoding='utf-8') as f:
        json.dump(synthesis, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Síntese completa salva: logs/saci_meta_FINAL_SYNTHESIS.json")
    
    # Criar relatório textual
    report = f"""
# RELATÓRIO FINAL - DEBATE SACI META-RECURSIVO
Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## DECISÃO CONSENSUAL
**Votação:** BUILD={build_votes}/4, BUY={buy_votes}/4, HYBRID={hybrid_votes}/4
**Consenso:** {synthesis['consensus']}

## RESUMO DAS 3 RODADAS

### RODADA 1: Propostas Iniciais (BUILD vs BUY)
"""
    
    for agent_key, data in round1_results.items():
        if data['success']:
            report += f"\n#### {data['agent_name']}\n"
            report += f"```\n{data['response'][:500]}...\n```\n"
    
    report += "\n### RODADA 2: Críticas Cruzadas\n"
    for agent_key, data in round2_results.items():
        if data['success']:
            report += f"\n#### {data['agent_name']}\n"
            report += f"```\n{data['response'][:500]}...\n```\n"
    
    report += "\n### RODADA 3: Convergência Final\n"
    for agent_key, data in round3_results.items():
        if data['success']:
            report += f"\n#### {data['agent_name']}\n"
            report += f"{data['response']}\n"
    
    with open('logs/saci_meta_FINAL_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Relatório textual salvo: logs/saci_meta_FINAL_REPORT.md")
    print("\n" + "="*80)
    print("DEBATE SACI CONCLUÍDO!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
