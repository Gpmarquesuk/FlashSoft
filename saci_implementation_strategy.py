"""
CONSULTA SACI - ESTRATÉGIA DE IMPLEMENTAÇÃO E IMPACTO DE MERCADO
Objetivo: Definir metodologia detalhada + análise competitiva profunda

RODADA 1: Propostas de Estratégia de Implementação
RODADA 2: Críticas às Metodologias
RODADA 3: Convergência + Relatório de Impacto de Mercado

DELIVERABLES:
1. Metodologia detalhada de implementação (step-by-step)
2. Relatório profundo: Como SACI se diferencia de produtos existentes
3. Análise de impacto no mercado de AI (disruptivo? incremental?)
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

# 4 especialistas (MODELOS ATUALIZADOS conforme solicitação)
AGENTS = {
    'claude_thinker': {
        'id': 'anthropic/claude-opus-4.5:thinking',
        'name': 'Claude 4.5 Thinker (Opus)',
        'specialty': 'Raciocínio profundo, análise estratégica'
    },
    'gpt5_codex': {
        'id': 'openai/gpt-5-codex',
        'name': 'GPT-5 Codex',
        'specialty': 'Implementação técnica, código de produção'
    },
    'gemini': {
        'id': 'google/gemini-2.5-pro',
        'name': 'Gemini 2.5 PRO',
        'specialty': 'Visão de mercado, benchmarking'
    },
    'grok': {
        'id': 'x-ai/grok-4',
        'name': 'Grok 4',
        'specialty': 'Perspectiva disruptiva, go-to-market'
    }
}

# Contexto do debate anterior
CONTEXT_PREVIOUS = """
CONTEXTO - DEBATE META-SACI ANTERIOR (consenso HYBRID 75%):

DECISÃO: Usar LangGraph + AutoGen + custom layer (~300 linhas)
- LangGraph: 60% (orquestração, state machines)
- AutoGen: 25% (multi-agent debate)
- Custom Layer: 15% (ConvergenceDetector, MetricsAggregator)

ANÁLISE COMPETITIVA:
- Devin: Não compete (IDE autônomo)
- AutoGen: 25% overlap (sem convergência forçada)
- LangGraph: 60% overlap (sem detecção de consenso)
- CrewAI: Task-oriented (não decision-oriented)
- GAP CRÍTICO: Convergência multi-métrica (semântica + votos + críticas) >= 75%

CONSENSO: SACI é FEATURE (não produto), mas vale POC de 3 semanas.
"""

# RODADA 1: Estratégia de Implementação
PROMPT_ROUND1 = f"""{CONTEXT_PREVIOUS}

# RODADA 1: ESTRATÉGIA DE IMPLEMENTAÇÃO DETALHADA

## CONTEXTO
O debate anterior concluiu que SACI deve ser HYBRID (LangGraph + AutoGen + custom layer).
Agora precisamos definir **COMO** implementar isso na prática.

## SUA TAREFA: METODOLOGIA DE IMPLEMENTAÇÃO

Crie uma **metodologia detalhada step-by-step** para implementar SACI HYBRID.

### PARTE A: Arquitetura Técnica Detalhada

1. **Estrutura de Módulos:**
   - Quais arquivos/classes criar?
   - Organização de pastas (`saci/`, `tests/`, etc)?
   - Interfaces entre componentes?

2. **Dependências e Stack:**
   - Versões exatas (LangGraph 0.x.x, AutoGen 0.x.x)?
   - Bibliotecas adicionais (sentence-transformers, scikit-learn)?
   - Configuração de ambiente (venv, requirements.txt)?

3. **Integração LangGraph + AutoGen:**
   - Como AutoGen agents se conectam aos LangGraph nodes?
   - State management (quais campos no StateGraph)?
   - Error handling e retries?

### PARTE B: Implementação do Custom Layer

**ConvergenceDetector** (~100 linhas):
- Input: List[str] (respostas dos 4 agentes)
- Output: ConvergenceMetrics (similarity, vote_alignment, critique_severity)
- Método: `is_converged() -> bool`
- Modelos NLP: qual sentence-transformer usar? (all-MiniLM-L6-v2? mpnet-base?)

**MetricsAggregator** (~100 linhas):
- Combinar 3 métricas (semântica, votos, críticas)
- Threshold: 2 de 3 >= 75%
- Logging de métricas (MLflow? Weights & Biases?)

**RoundOrchestrator** (~100 linhas):
- Gerenciar 5 rounds (ou 3, dado que meta-debate provou 5 é over-engineering?)
- Conditional edges: convergiu? → vote : refinement
- Context management (evitar context window overflow)

### PARTE C: Roadmap de Implementação (3 Semanas)

**Semana 1: Foundation**
- Dia 1-2: Setup (LangGraph + AutoGen instalação, hello world)
- Dia 3-4: ConvergenceDetector básico (cosine similarity apenas)
- Dia 5: Integração LangGraph StateGraph com 3 nós (Propose → Critique → Vote)

**Semana 2: Core Features**
- Dia 6-7: MetricsAggregator (adicionar votos + críticas)
- Dia 8-9: RoundOrchestrator (loop de 3 rounds)
- Dia 10: Testes unitários (pytest, cobertura >= 80%)

**Semana 3: Validação**
- Dia 11-13: 10 debates reais (decisões arquiteturais)
- Dia 14: Análise GO/NO-GO (métricas de sucesso)
- Dia 15: Relatório final + decisão de produtização

### PARTE D: Análise de Riscos

1. **Riscos Técnicos:**
   - LangGraph + AutoGen incompatibilidade?
   - Sentence-transformers lento para convergência?
   - Context overflow em debates longos?

2. **Mitigações:**
   - Versões específicas testadas?
   - Caching de embeddings?
   - Truncamento inteligente de contexto?

## FORMATO DE RESPOSTA

```markdown
# METODOLOGIA DE IMPLEMENTAÇÃO SACI

## 1. ARQUITETURA
[Diagrama/descrição de módulos]

## 2. STACK TÉCNICO
- LangGraph: [versão]
- AutoGen: [versão]
- Outros: [lista]

## 3. CUSTOM LAYER (pseudo-código)
```python
class ConvergenceDetector:
    def check(self, responses: List[str]) -> ConvergenceMetrics:
        # [implementação detalhada]
```

## 4. ROADMAP (3 semanas)
Semana 1: [detalhar]
Semana 2: [detalhar]
Semana 3: [detalhar]

## 5. RISCOS E MITIGAÇÕES
[lista]

## 6. ESTIMATIVA DE ESFORÇO
[horas/pessoa, complexidade]
```

Máximo: 2000 tokens.
"""

# RODADA 2: Críticas às Metodologias
def build_critique_prompt(all_proposals: dict) -> str:
    proposals_text = "\n\n".join([
        f"{'='*80}\n"
        f"METODOLOGIA DE {data['agent_name'].upper()}:\n"
        f"{'='*80}\n"
        f"{data['response']}"
        for key, data in all_proposals.items()
    ])
    
    return f"""{CONTEXT_PREVIOUS}

# RODADA 2: CRÍTICA ÀS METODOLOGIAS

Você viu as 4 metodologias de implementação:

{proposals_text}

## SUA TAREFA: CRÍTICA TÉCNICA PROFUNDA

Para CADA metodologia dos outros 3 agentes:

### 1. ANÁLISE DE VIABILIDADE
- A arquitetura proposta é viável? (complexidade, dependências)
- O roadmap de 3 semanas é realista?
- Há over-engineering ou under-engineering?

### 2. GAPS TÉCNICOS
- O que faltou detalhar? (integrações, error handling?)
- Riscos não considerados?
- Trade-offs não explorados?

### 3. COMPARAÇÃO COMPETITIVA
- Como essa metodologia compara com implementar usando apenas LangGraph?
- E com usar apenas AutoGen?
- E com usar CrewAI do zero?

### 4. SUGESTÕES DE MELHORIA
- Mudanças na arquitetura?
- Simplificações possíveis?
- Otimizações de performance?

## FORMATO

```
CRÍTICA À METODOLOGIA [NOME]:

VIABILIDADE: [realista | otimista | pessimista]
- [análise]

GAPS:
- [o que faltou]

COMPARAÇÃO vs ALTERNATIVAS:
- vs LangGraph puro: [análise]
- vs AutoGen puro: [análise]

SUGESTÕES:
- [melhorias específicas]

SEVERIDADE: [minor | moderate | critical]
```

Repita para cada metodologia.

Máximo: 2500 tokens.
"""

# RODADA 3: Convergência + Análise de Impacto de Mercado
def build_convergence_prompt(proposals: dict, critiques: dict) -> str:
    all_content = f"""
RODADA 1 - METODOLOGIAS:
{json.dumps({k: v['response'][:600] + '...' for k, v in proposals.items()}, indent=2, ensure_ascii=False)}

RODADA 2 - CRÍTICAS:
{json.dumps({k: v['response'][:600] + '...' for k, v in critiques.items()}, indent=2, ensure_ascii=False)}
"""
    
    return f"""{CONTEXT_PREVIOUS}

# RODADA 3: CONVERGÊNCIA + ANÁLISE DE IMPACTO DE MERCADO

{all_content}

## PARTE 1: CONVERGÊNCIA DE METODOLOGIA

Sintetize uma **METODOLOGIA FINAL CONSOLIDADA** baseada nas 4 propostas e críticas:

1. **CONSENSO ARQUITETURAL:**
   - Estrutura de módulos (maioria concorda?)
   - Stack técnico (versões, dependências)
   - Custom layer (ConvergenceDetector, MetricsAggregator, RoundOrchestrator)

2. **ROADMAP CONSENSUAL (3 semanas):**
   - Semana 1: [o que 3+ agentes concordam]
   - Semana 2: [o que 3+ agentes concordam]
   - Semana 3: [o que 3+ agentes concordam]

3. **RISCOS E MITIGAÇÕES PRIORITÁRIAS:**
   - Top 3 riscos (mais mencionados)
   - Top 3 mitigações (consensuais)

## PARTE 2: RELATÓRIO DE IMPACTO DE MERCADO (CRÍTICO!)

Agora, faça uma **ANÁLISE PROFUNDA** de como SACI se diferencia e impacta o mercado:

### A) POSICIONAMENTO COMPETITIVO

**vs Devin (Cognition Labs):**
- Devin: IDE autônomo end-to-end ($500/mês, foco em coding)
- SACI: Framework de debate multi-IA (open-source?)
- **Diferencial único:** [o que SACI faz que Devin não faz?]
- **Overlap:** [onde competem? 0%? 10%?]
- **Market share potencial:** [SACI rouba usuários de Devin? Ou é mercado diferente?]

**vs AutoGen (Microsoft):**
- AutoGen: Open-source, multi-agent orchestration
- SACI: AutoGen + convergência forçada
- **Diferencial único:** [convergência multi-métrica, mas isso basta para ser produto separado?]
- **Overlap:** [85%? AutoGen pode adicionar isso como feature?]
- **Cenário futuro:** [Microsoft adiciona convergência no AutoGen v0.3? SACI se torna obsoleta?]

**vs LangGraph (LangChain):**
- LangGraph: State machine para agentes ($0 open-source, $X enterprise)
- SACI: LangGraph + custom convergence
- **Diferencial único:** [lógica dos 5 rounds, mas LangGraph pode fazer isso em tutorial?]
- **Overlap:** [90%? LangGraph cookbook já mostra isso?]
- **Ameaça:** [LangGraph lança "Convergence Pattern" e mata SACI?]

**vs CrewAI:**
- CrewAI: Task-oriented agents (open-source)
- SACI: Decision-oriented (não task execution)
- **Diferencial único:** [debate estruturado vs task pipelines]
- **Overlap:** [20%? Mercados diferentes?]
- **Oportunidade:** [SACI para decisões estratégicas, CrewAI para execução?]

### B) ANÁLISE DE DISRUPÇÃO

**Classifique SACI:**

- [ ] **DISRUPTIVO** (cria novo mercado, como ChatGPT criou conversational AI)
- [ ] **INCREMENTAL** (melhora existente, como GPT-4 vs GPT-3.5)
- [ ] **FEATURE** (deveria ser parte de produto maior, não standalone)
- [ ] **REDUNDANTE** (já existe equivalente no mercado)

**Justificativa:** [3 parágrafos técnicos]

### C) IMPACTO NO MERCADO DE AI

**Se SACI for lançado hoje (open-source), o que acontece?**

1. **Adoção potencial (12 meses):**
   - Usuários: [0-100? 100-1k? 1k-10k? 10k+?]
   - Empresas: [startups? enterprises? research labs?]
   - Casos de uso: [quais indústrias adotariam primeiro?]

2. **Resposta dos competidores:**
   - Microsoft (AutoGen): [adiciona convergência em 3 meses? ignora?]
   - LangChain (LangGraph): [lança cookbook? ignora?]
   - Anthropic/OpenAI: [relevante para eles?]

3. **Cenário 5 anos:**
   - **Melhor caso:** [SACI vira padrão de debates multi-IA, 50k+ usuários]
   - **Caso base:** [nicho acadêmico/research, 500 usuários]
   - **Pior caso:** [Microsoft absorve conceito, SACI abandonada]

### D) VEREDITO FINAL

```
DIFERENCIAL DE SACI vs MERCADO:
[resumo 1 parágrafo]

IMPACTO ESPERADO:
- Curto prazo (6 meses): [baixo | médio | alto]
- Longo prazo (5 anos): [baixo | médio | alto]

RECOMENDAÇÃO:
- [ ] LANÇAR como produto open-source standalone
- [ ] LANÇAR como biblioteca/plugin para LangGraph/AutoGen
- [ ] NÃO LANÇAR (contribuir feature para AutoGen/LangGraph upstream)
- [ ] PIVOTAR para [outra direção]

CONFIANÇA: [0-100%]
```

## FORMATO DE RESPOSTA

```markdown
# PARTE 1: METODOLOGIA CONSENSUAL

[síntese das 4 metodologias]

# PARTE 2: RELATÓRIO DE IMPACTO DE MERCADO

## Posicionamento Competitivo
[análise profunda vs Devin, AutoGen, LangGraph, CrewAI]

## Classificação de Disrupção
[DISRUPTIVO | INCREMENTAL | FEATURE | REDUNDANTE]

## Impacto no Mercado AI
[adoção, resposta competidores, cenário 5 anos]

## Veredito Final
[recomendação + confiança]
```

Máximo: 2500 tokens.
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
You are participating in a SACI debate about implementation strategy and market impact.
Be deeply technical, analytical, and strategic. Provide actionable insights."""
    
    try:
        print(f"⏳ Enviando prompt (rodada {round_num})...")
        
        # Ajustar max_tokens por rodada
        max_tokens_map = {1: 2000, 2: 2500, 3: 2500}
        
        response = chat(
            model=agent_id,
            system=system_prompt,
            user=prompt,
            max_tokens=max_tokens_map.get(round_num, 2000),
            temperature=0.2  # Baixo para análise técnica
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
    filename = f"logs/saci_impl_round{round_num}_{filename_prefix}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"  💾 Salvo: {filename}")
    
    # Salvar também em TXT para fácil leitura
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
    print("CONSULTA SACI - ESTRATÉGIA DE IMPLEMENTAÇÃO E IMPACTO DE MERCADO")
    print("="*80 + "\n")
    
    print("Agentes participantes (MODELOS ATUALIZADOS):")
    for key, info in AGENTS.items():
        print(f"  • {info['name']} - {info['specialty']}")
    print("\n")
    
    # ============================================================
    # RODADA 1: METODOLOGIAS DE IMPLEMENTAÇÃO
    # ============================================================
    print("\n" + "="*80)
    print("FASE 1: METODOLOGIAS DE IMPLEMENTAÇÃO")
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
            print("\n⏸  Aguardando 5s...")
            time.sleep(5)
    
    save_results(1, round1_results, "methodologies")
    
    # ============================================================
    # RODADA 2: CRÍTICAS TÉCNICAS
    # ============================================================
    print("\n\n" + "="*80)
    print("FASE 2: CRÍTICAS TÉCNICAS ÀS METODOLOGIAS")
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
            print("\n⏸  Aguardando 5s...")
            time.sleep(5)
    
    save_results(2, round2_results, "critiques")
    
    # ============================================================
    # RODADA 3: CONVERGÊNCIA + IMPACTO DE MERCADO
    # ============================================================
    print("\n\n" + "="*80)
    print("FASE 3: CONVERGÊNCIA + ANÁLISE DE IMPACTO DE MERCADO")
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
            print("\n⏸  Aguardando 5s...")
            time.sleep(5)
    
    save_results(3, round3_results, "convergence_market")
    
    # ============================================================
    # SÍNTESE FINAL
    # ============================================================
    print("\n\n" + "="*80)
    print("SÍNTESE FINAL - IMPLEMENTAÇÃO + IMPACTO DE MERCADO")
    print("="*80 + "\n")
    
    # Análise de convergência na metodologia
    print("📊 ANÁLISE DE CONSENSO (Metodologia):\n")
    
    methodologies_summary = {}
    for agent_key, data in round1_results.items():
        if data['success']:
            response = data['response']
            # Tentar extrair stack técnico
            if 'langgraph' in response.lower():
                methodologies_summary.setdefault('usa_langgraph', 0)
                methodologies_summary['usa_langgraph'] += 1
            if 'autogen' in response.lower():
                methodologies_summary.setdefault('usa_autogen', 0)
                methodologies_summary['usa_autogen'] += 1
            if '3 semanas' in response.lower() or 'three weeks' in response.lower():
                methodologies_summary.setdefault('roadmap_3_semanas', 0)
                methodologies_summary['roadmap_3_semanas'] += 1
    
    print(f"  • LangGraph mencionado: {methodologies_summary.get('usa_langgraph', 0)}/4 agentes")
    print(f"  • AutoGen mencionado: {methodologies_summary.get('usa_autogen', 0)}/4 agentes")
    print(f"  • Roadmap 3 semanas: {methodologies_summary.get('roadmap_3_semanas', 0)}/4 agentes")
    
    # Análise de impacto de mercado
    print("\n📊 ANÁLISE DE IMPACTO DE MERCADO:\n")
    
    market_votes = {'disruptivo': 0, 'incremental': 0, 'feature': 0, 'redundante': 0}
    launch_recommendations = {'lancar_standalone': 0, 'lancar_plugin': 0, 'nao_lancar': 0, 'pivotar': 0}
    
    for agent_key, data in round3_results.items():
        if data['success']:
            response_lower = data['response'].lower()
            
            # Classificação de disrupção
            if 'disruptivo' in response_lower or 'disruptive' in response_lower:
                market_votes['disruptivo'] += 1
            elif 'incremental' in response_lower:
                market_votes['incremental'] += 1
            elif 'feature' in response_lower and 'não' not in response_lower.split('feature')[0][-20:]:
                market_votes['feature'] += 1
            elif 'redundante' in response_lower or 'redundant' in response_lower:
                market_votes['redundante'] += 1
            
            # Recomendação de lançamento
            if 'lançar' in response_lower and 'standalone' in response_lower:
                launch_recommendations['lancar_standalone'] += 1
            elif 'plugin' in response_lower or 'biblioteca' in response_lower:
                launch_recommendations['lancar_plugin'] += 1
            elif 'não lançar' in response_lower or 'do not launch' in response_lower:
                launch_recommendations['nao_lancar'] += 1
            elif 'pivotar' in response_lower or 'pivot' in response_lower:
                launch_recommendations['pivotar'] += 1
    
    print("  Classificação de Disrupção:")
    for key, count in market_votes.items():
        if count > 0:
            print(f"    • {key.upper()}: {count}/4 agentes")
    
    print("\n  Recomendação de Lançamento:")
    for key, count in launch_recommendations.items():
        if count > 0:
            print(f"    • {key.replace('_', ' ').upper()}: {count}/4 agentes")
    
    # Salvar síntese
    synthesis = {
        'timestamp': datetime.now().isoformat(),
        'agents': list(AGENTS.keys()),
        'methodologies_consensus': methodologies_summary,
        'market_impact': {
            'disruption_classification': market_votes,
            'launch_recommendations': launch_recommendations
        },
        'round1_methodologies': round1_results,
        'round2_critiques': round2_results,
        'round3_convergence_market': round3_results
    }
    
    with open('logs/saci_impl_FINAL_SYNTHESIS.json', 'w', encoding='utf-8') as f:
        json.dump(synthesis, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Síntese completa salva: logs/saci_impl_FINAL_SYNTHESIS.json")
    
    # Criar relatório executivo
    report = f"""
# RELATÓRIO FINAL - ESTRATÉGIA DE IMPLEMENTAÇÃO E IMPACTO DE MERCADO SACI
Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## MODELOS CONSULTADOS
- {AGENTS['claude_thinker']['name']} (raciocínio profundo)
- {AGENTS['gpt5_codex']['name']} (implementação técnica)
- {AGENTS['gemini']['name']} (visão de mercado)
- {AGENTS['grok']['name']} (perspectiva disruptiva)

## CONSENSO METODOLÓGICO
"""
    
    for key, value in methodologies_summary.items():
        report += f"- {key.replace('_', ' ').title()}: {value}/4 agentes\n"
    
    report += "\n## CLASSIFICAÇÃO DE DISRUPÇÃO\n"
    max_votes = max(market_votes.values())
    for key, count in market_votes.items():
        if count == max_votes:
            report += f"**{key.upper()}**: {count}/4 agentes (CONSENSO)\n"
        elif count > 0:
            report += f"- {key.title()}: {count}/4 agentes\n"
    
    report += "\n## RECOMENDAÇÃO DE LANÇAMENTO\n"
    max_launch = max(launch_recommendations.values()) if launch_recommendations else 0
    for key, count in launch_recommendations.items():
        if count == max_launch:
            report += f"**{key.replace('_', ' ').upper()}**: {count}/4 agentes (CONSENSO)\n"
        elif count > 0:
            report += f"- {key.replace('_', ' ').title()}: {count}/4 agentes\n"
    
    report += "\n\n---\n\n"
    report += "## RODADA 1: METODOLOGIAS DE IMPLEMENTAÇÃO\n\n"
    
    for agent_key, data in round1_results.items():
        if data['success']:
            report += f"### {data['agent_name']}\n\n"
            report += f"{data['response'][:1000]}...\n\n"
    
    report += "\n## RODADA 2: CRÍTICAS TÉCNICAS\n\n"
    
    for agent_key, data in round2_results.items():
        if data['success']:
            report += f"### {data['agent_name']}\n\n"
            report += f"{data['response'][:1000]}...\n\n"
    
    report += "\n## RODADA 3: CONVERGÊNCIA + IMPACTO DE MERCADO\n\n"
    
    for agent_key, data in round3_results.items():
        if data['success']:
            report += f"### {data['agent_name']}\n\n"
            report += f"{data['response']}\n\n"
    
    with open('logs/saci_impl_FINAL_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Relatório executivo salvo: logs/saci_impl_FINAL_REPORT.md")
    print("\n" + "="*80)
    print("DEBATE SACI CONCLUÍDO!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
