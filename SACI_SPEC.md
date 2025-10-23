# SACI - Sistema Avançado de Convergência de Ideias

**Versão:** 1.0  
**Data:** 2025-10-23  
**Baseado em:** Consulta a 4 especialistas (Gemini 2.5 PRO, GPT-5 CODEX, Grok 4, Claude 3.5 Sonnet)

---

## 📋 SUMÁRIO EXECUTIVO

### O que é a SACI?
Sistema de debate estruturado entre 4 modelos de IA que convergem iterativamente até obter **consenso majoritário** (3 de 4) sobre soluções para problemas complexos.

### Por que criar?
- Soluções por agente único são limitadas e enviesadas
- Consultas paralelas não produzem convergência real
- Problemas críticos da FlashSoft exigem "inteligência coletiva"

### Aplicações
- Decisões arquiteturais críticas
- Debugging de problemas complexos  
- Design de componentes-chave
- Validação de estratégias
- **Uso imediato:** Validar recomendações anteriores sobre a fábrica

---

## 🏗️ ARQUITETURA CONSENSUAL

### **CONSENSO DOS 4 ESPECIALISTAS:**

#### 1. Estrutura de Orquestrador Centralizado
**Todos concordam:** Motor central que gerencia:
- Estado do debate (histórico, propostas, votos)
- Progressão de fases
- Detecção de convergência
- Persistência e logging

#### 2. Protocolo de 3-5 Rodadas
**Convergência:**
- **Mínimo:** 3 rodadas (proposta → crítica → refinamento)
- **Máximo:** 5 rodadas (evita loops infinitos)
- **Ideal:** 4 rodadas com convergência em rodada 3-4

#### 3. Fases do Debate
**Consenso sobre estrutura:**
1. **Initial Proposal** (Rodada 1): Cada agente propõe solução independente
2. **Critique** (Rodada 2): Agentes criticam propostas dos outros (strengths/weaknesses)
3. **Refinement** (Rodada 3): Agentes refinam propostas baseado em críticas
4. **Convergence** (Rodada 4): Síntese colaborativa
5. **Final Vote** (Rodada 5): Votação com justificativas

#### 4. Detecção de Convergência
**Métricas múltiplas** (não apenas votação):
- **Similaridade semântica** entre propostas (embeddings + cosine similarity)
- **Alinhamento de votos** (>= 75% concordam)
- **Severidade de críticas** (redução ao longo das rodadas)
- **Delta entre iterações** (mudanças diminuem)

**Convergência detectada quando:** 2+ métricas > 75% threshold

---

## 🤖 SELEÇÃO DOS 4 MODELOS

### **RECOMENDAÇÃO CONSENSUAL:**

| Posição | Modelo | Justificativa |
|---------|--------|---------------|
| **Agente 1** | **Claude 3.5 Sonnet** | Raciocínio profundo, críticas construtivas |
| **Agente 2** | **GPT-4o** (ou O1 Pro) | Análise balanceada, sintetização |
| **Agente 3** | **Gemini 2.5 Pro** | Visão técnica, arquitetura |
| **Agente 4** | **Grok 4** (ou Codex) | Perspectiva alternativa, code-focused |

### Critérios de Seleção:
- ✅ **Diversidade de "famílias"** (Anthropic, OpenAI, Google, xAI)
- ✅ **Especialidades complementares**
- ✅ **Suporte a structured output** (JSON native)
- ✅ **Context window adequado** (100k+ tokens)

---

## 🔧 IMPLEMENTAÇÃO TÉCNICA

### Stack Recomendado (Consenso):
```python
# Core
- Python 3.11+
- Pydantic v2 (structured data + validation)
- asyncio (debates assíncronos)

# LLM Orchestration
- OpenAI SDK (para todos via OpenRouter)
- tenacity (retry logic)

# Convergência
- sentence-transformers (embeddings para similaridade)
- scikit-learn (cosine similarity)

# Persistência
- SQLModel (ORM com Pydantic)
- SQLite (desenvolvimento) → PostgreSQL (produção)

# Monitoring
- structlog (logging estruturado)
- MLflow (tracking de debates)
```

### Estrutura de Dados Core (Pydantic):

```python
from typing import List, Dict, Literal
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class DebatePhase(str, Enum):
    INITIAL_PROPOSAL = "initial_proposal"
    CRITIQUE = "critique"
    REFINEMENT = "refinement"
    CONVERGENCE = "convergence"
    FINAL_VOTE = "final_vote"

class Proposal(BaseModel):
    """Proposta de solução de um agente"""
    id: str
    agent_id: str
    content: str  # Solução proposta
    reasoning: str  # Justificativa
    phase: DebatePhase
    timestamp: datetime
    references: List[str] = []  # IDs de propostas influentes
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)

class Critique(BaseModel):
    """Crítica estruturada de uma proposta"""
    critic_id: str
    target_proposal_id: str
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    severity: Literal["minor", "moderate", "critical"]

class Vote(BaseModel):
    """Voto em proposta final"""
    voter_id: str
    proposal_id: str
    support: Literal["strong_agree", "agree", "neutral", "disagree", "strong_disagree"]
    reasoning: str

class ConvergenceMetrics(BaseModel):
    """Métricas de convergência"""
    round: int
    proposal_similarity: float  # 0-1
    vote_alignment: float  # 0-1
    critique_severity: float  # 0-1 (média)
    consensus_strength: float  # 0-1 (combinação)
    
    def is_converged(self, threshold: float = 0.75) -> bool:
        """Convergido quando >=2 métricas > threshold"""
        metrics = [
            self.proposal_similarity,
            self.vote_alignment,
            1 - self.critique_severity  # Invertido
        ]
        return sum(m > threshold for m in metrics) >= 2

class DebateResult(BaseModel):
    """Resultado final do debate"""
    problem: str
    consensus_proposal: Proposal
    convergence_metrics: ConvergenceMetrics
    rounds_taken: int
    total_duration_seconds: float
    votes: List[Vote]
    debate_history: List[Dict]  # Log completo
```

---

## 🔄 PROTOCOLO DE DEBATE DETALHADO

### **Rodada 1: Initial Proposal**
```
Para cada agente (paralelo):
  Prompt: "Analise o problema: {problem}. Proponha solução detalhada."
  Output: Proposal(content, reasoning, confidence)
```

### **Rodada 2: Critique**
```
Para cada agente:
  Context: Todas as 4 propostas da Rodada 1
  Prompt: "Critique as propostas dos outros. Identifique strengths, weaknesses, suggestions."
  Output: List[Critique] (3 críticas, uma para cada proposta dos outros)
```

### **Rodada 3: Refinement**
```
Para cada agente:
  Context: Sua proposta original + críticas recebidas
  Prompt: "Refine sua proposta baseado nas críticas. Incorpore sugestões válidas."
  Output: Proposal(refined_content, reasoning)
```

### **Rodada 4: Convergence Check**
```
Sistema calcula:
  - Similaridade entre propostas refinadas (embeddings)
  - Identificação de proposta mais próxima do consenso
  
Se convergência >= 75%:
  → Prossegue para Rodada 5
Senão:
  → Rodada extra de síntese forçada (facilitador Gemini)
```

### **Rodada 5: Final Vote**
```
Para cada agente:
  Context: Proposta de consenso identificada
  Prompt: "Vote na proposta final: strong_agree|agree|neutral|disagree|strong_disagree + justificativa"
  Output: Vote

Critério de aceitação: >= 3 agentes com agree ou strong_agree
```

---

## 🎯 MECANISMOS DE DESEMPATE

### **CONSENSO DOS ESPECIALISTAS:**

1. **Empate 2 vs 2:**
   - **Opção A (preferida):** Convocar 5º modelo especializado (ex: GPT-5 Codex para código, O1 Pro para raciocínio)
   - **Opção B:** Human-in-the-loop (usuário decide)
   - **Opção C:** Usar métricas de convergência (proposta com maior similaridade semântica)

2. **Sem convergência após 5 rodadas:**
   - **Opção A:** Declarar "no consensus" e apresentar 2-3 melhores propostas ao usuário
   - **Opção B:** Rodada de "forced synthesis" (Gemini como facilitador cria síntese híbrida)
   - **Opção C:** Reduzir escopo do problema e tentar novamente

3. **Divergência crescente:**
   - Sistema detecta se críticas ficam mais severas entre rodadas
   - Se detectado: pausa automática, reformula problema com mais contexto, reinicia

---

## 💻 PSEUDOCÓDIGO IMPLEMENTAÇÃO

```python
class SACIEngine:
    def __init__(self, agents: List[Agent], max_rounds=5, threshold=0.75):
        self.agents = agents
        self.max_rounds = max_rounds
        self.threshold = threshold
        self.debate_history = []
        
    async def run_debate(self, problem: str) -> DebateResult:
        """Executa debate completo até convergência"""
        
        # RODADA 1: Propostas iniciais
        proposals = await self.round_initial_proposals(problem)
        
        # RODADA 2: Críticas
        critiques = await self.round_critiques(proposals)
        
        # RODADA 3: Refinamento
        refined_proposals = await self.round_refinement(proposals, critiques)
        
        # RODADA 4: Check convergência
        metrics = self.calculate_convergence(refined_proposals)
        
        if metrics.is_converged(self.threshold):
            # Convergiu! Identifica proposta consenso
            consensus_prop = self.identify_consensus_proposal(refined_proposals)
        else:
            # Não convergiu - forçar síntese
            consensus_prop = await self.forced_synthesis(refined_proposals)
        
        # RODADA 5: Votação final
        votes = await self.round_final_vote(consensus_prop)
        
        # Validar resultado
        if self.validate_votes(votes):
            return DebateResult(
                problem=problem,
                consensus_proposal=consensus_prop,
                convergence_metrics=metrics,
                rounds_taken=4 if metrics.is_converged() else 5,
                votes=votes,
                debate_history=self.debate_history
            )
        else:
            # Desempate necessário
            return await self.handle_tie(problem, votes)
    
    async def round_initial_proposals(self, problem: str) -> List[Proposal]:
        """Rodada 1: Cada agente propõe solução"""
        tasks = [agent.propose(problem) for agent in self.agents]
        proposals = await asyncio.gather(*tasks)
        self.debate_history.append({"round": 1, "phase": "proposals", "data": proposals})
        return proposals
    
    async def round_critiques(self, proposals: List[Proposal]) -> List[Critique]:
        """Rodada 2: Agentes criticam propostas dos outros"""
        critiques = []
        for agent in self.agents:
            # Cada agente vê todas as propostas exceto a própria
            other_proposals = [p for p in proposals if p.agent_id != agent.id]
            agent_critiques = await agent.critique(other_proposals)
            critiques.extend(agent_critiques)
        
        self.debate_history.append({"round": 2, "phase": "critiques", "data": critiques})
        return critiques
    
    async def round_refinement(self, proposals: List[Proposal], 
                               critiques: List[Critique]) -> List[Proposal]:
        """Rodada 3: Agentes refinam baseado em críticas"""
        refined = []
        for agent in self.agents:
            # Filtrar críticas recebidas por esse agente
            my_critiques = [c for c in critiques 
                           if any(p.id == c.target_proposal_id and p.agent_id == agent.id 
                                  for p in proposals)]
            
            my_proposal = next(p for p in proposals if p.agent_id == agent.id)
            refined_prop = await agent.refine(my_proposal, my_critiques)
            refined.append(refined_prop)
        
        self.debate_history.append({"round": 3, "phase": "refinement", "data": refined})
        return refined
    
    def calculate_convergence(self, proposals: List[Proposal]) -> ConvergenceMetrics:
        """Calcula métricas de convergência"""
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Embeddings das propostas
        contents = [p.content for p in proposals]
        embeddings = model.encode(contents)
        
        # Similaridade par a par
        similarities = cosine_similarity(embeddings)
        avg_similarity = similarities[np.triu_indices_from(similarities, k=1)].mean()
        
        # Outras métricas (simplificado)
        avg_confidence = np.mean([p.confidence for p in proposals])
        
        return ConvergenceMetrics(
            round=3,
            proposal_similarity=float(avg_similarity),
            vote_alignment=0.0,  # Calculado na rodada 5
            critique_severity=0.3,  # Estimado
            consensus_strength=float(avg_similarity * avg_confidence)
        )
    
    def identify_consensus_proposal(self, proposals: List[Proposal]) -> Proposal:
        """Identifica proposta mais próxima do consenso"""
        # Usa similaridade semântica para encontrar "centroide"
        # Simplificado: retorna proposta com maior confidence
        return max(proposals, key=lambda p: p.confidence)
    
    async def round_final_vote(self, consensus: Proposal) -> List[Vote]:
        """Rodada 5: Votação final"""
        tasks = [agent.vote(consensus) for agent in self.agents]
        votes = await asyncio.gather(*tasks)
        self.debate_history.append({"round": 5, "phase": "votes", "data": votes})
        return votes
    
    def validate_votes(self, votes: List[Vote]) -> bool:
        """Valida se há consenso majoritário"""
        positive_votes = sum(1 for v in votes 
                            if v.support in ["agree", "strong_agree"])
        return positive_votes >= 3  # Maioria
    
    async def handle_tie(self, problem: str, votes: List[Vote]) -> DebateResult:
        """Desempate com 5º modelo"""
        tiebreaker_agent = Agent(model="openai/o1-pro", id="tiebreaker")
        
        # Contexto: problema + 4 votos
        tiebreaker_vote = await tiebreaker_agent.vote_with_context(
            problem=problem,
            votes=votes
        )
        
        # Retorna com flag de tiebreaker
        # ... (implementação completa)
```

---

## 🚀 EXEMPLO DE USO PRÁTICO

### Caso 1: Validar Recomendações Anteriores sobre Fábrica

```python
# Inicializar SACI
saci = SACIEngine(
    agents=[
        Agent(model="anthropic/claude-sonnet-4.5", id="claude"),
        Agent(model="openai/gpt-4o", id="gpt4o"),
        Agent(model="google/gemini-2.5-pro", id="gemini"),
        Agent(model="x-ai/grok-4", id="grok")
    ],
    max_rounds=5,
    threshold=0.75
)

# Definir problema
problem = """
A junta de especialistas recomendou:
1. Fixar Planner com Pydantic schema
2. Reduzir context window drasticamente
3. Simplificar committee de modelos
4. Criar UI com Streamlit

O usuário questiona: "Não estou convencido de que esta é a melhor estratégia."

TAREFA SACI:
- Debater se essas recomendações são realmente ótimas
- Propor alternativas se houver consenso de que não são
- Convergir em estratégia final validada por 4 modelos
"""

# Executar debate
result = await saci.run_debate(problem)

# Resultado
print(f"✓ Consenso alcançado em {result.rounds_taken} rodadas")
print(f"✓ Força do consenso: {result.convergence_metrics.consensus_strength:.0%}")
print(f"\n📝 SOLUÇÃO CONSENSUAL:\n{result.consensus_proposal.content}")
print(f"\n📊 VOTAÇÃO:")
for vote in result.votes:
    print(f"  {vote.voter_id}: {vote.support} - {vote.reasoning[:100]}...")
```

### Caso 2: Decisão Arquitetural da Fábrica

```python
problem = """
Decisão crítica: Formato de saída do Planner

OPÇÕES:
A) JSON com código completo: {"patches": [{"path": "...", "content": "..."}]}
B) Unified diff patches (git diff format)
C) Geração direta de arquivos .py no workspace (sem JSON)
D) Chunks estruturados com AST patches

Considerar:
- Context window limits
- Facilidade de parsing
- Robustez a erros
- Token efficiency

SACI: Convergir na melhor opção com justificativa técnica.
"""

result = await saci.run_debate(problem)
# Implementar solução escolhida com confiança
```

---

## 📅 ROADMAP DE IMPLEMENTAÇÃO

### **FASE 1: MVP (2-3 dias)**
- [ ] Implementar Pydantic models (Proposal, Critique, Vote, Metrics)
- [ ] Motor básico com 3 rodadas (propose → critique → vote)
- [ ] Integração com OpenRouter (4 modelos via llm_client.py)
- [ ] Cálculo simples de convergência (votação majoritária)
- [ ] Teste com problema "toy" (ex: escolher nome de variável)

### **FASE 2: Core Completo (3-5 dias)**
- [ ] 5 rodadas completas com refinement
- [ ] Embeddings + cosine similarity para convergência semântica
- [ ] Persistência com SQLModel
- [ ] Logging estruturado (structlog)
- [ ] Mecanismo de desempate (5º modelo)
- [ ] Teste com problema real da fábrica

### **FASE 3: Produção (5-7 dias)**
- [ ] Timeout handling e retry logic
- [ ] UI com Streamlit para monitorar debates
- [ ] API FastAPI para integração externa
- [ ] MLflow tracking de debates
- [ ] Documentação completa
- [ ] Deploy como serviço standalone

---

## 🎯 APLICAÇÃO IMEDIATA À FÁBRICA FLASHSOFT

### **Uso da SACI para Validar Estratégia Atual:**

```python
# 1. Executar SACI sobre o próprio problema da fábrica
problem_fabrica = """
CONTEXTO: FlashSoft factory falha 100% no Planner (Context Window Overflow).

RECOMENDAÇÕES ANTERIORES:
- Pydantic schema para Planner output
- Truncar spec em 15 linhas
- Limitar a 2 arquivos
- Few-shot examples no prompt

QUESTÃO: Essa estratégia resolverá o problema raiz ou é apenas paliativo?

ALTERNATIVAS A CONSIDERAR:
1. Refatorar Planner em sub-agentes (1 por arquivo)
2. Usar diffs em vez de JSON com código completo
3. Geração incremental com validação a cada arquivo
4. Modelo especializado (Codex) em vez de Claude/Gemini

SACI: Convergir na estratégia DEFINITIVA para o Planner.
"""

resultado = await saci.run_debate(problem_fabrica)

# 2. Implementar solução consensual com confiança
implementar_solucao(resultado.consensus_proposal)
```

### **Vantagens da SACI vs Consulta Paralela Anterior:**
- ✅ **Convergência real** (não apenas 3 opiniões independentes)
- ✅ **Refinamento iterativo** (propostas melhoram com críticas)
- ✅ **Validação cruzada** (cada agente avalia os outros)
- ✅ **Consenso fundamentado** (>=75% alignment em múltiplas métricas)
- ✅ **Rastreabilidade** (histórico completo do debate)

---

## 📚 REFERÊNCIAS TÉCNICAS

### Frameworks Multi-Agent Consultados:
- **AutoGen** (Microsoft): https://github.com/microsoft/autogen
- **LangGraph** (LangChain): https://github.com/langchain-ai/langgraph
- **CrewAI**: https://github.com/joaomdmoura/crewAI

### Papers Acadêmicos:
- "Multi-Agent Debate" (Du et al., 2023): https://arxiv.org/abs/2305.14325
- "ReAct: Synergizing Reasoning and Acting in LLMs" (Yao et al., 2022)
- "Constitutional AI" (Anthropic): Debate interno entre modelos

### Consensus Algorithms:
- Raft (consensus for distributed systems)
- Paxos (Byzantine fault tolerance)
- Majority voting with confidence weighting

---

## 🏁 PRÓXIMOS PASSOS IMEDIATOS

1. **HOJE:**
   - ✅ Consulta META concluída (4/4 especialistas)
   - ✅ Especificação SACI criada
   - [ ] Revisar e aprovar spec com usuário

2. **AMANHÃ:**
   - [ ] Implementar Pydantic models (SACI_SPEC → código)
   - [ ] Motor MVP com 3 rodadas
   - [ ] Teste com problema toy

3. **DIA 3:**
   - [ ] Rodar SACI sobre problema da fábrica
   - [ ] Implementar solução consensual
   - [ ] Validar com execução real

---

## 📊 MÉTRICAS DE SUCESSO

### Curto Prazo (1 semana)
- [ ] SACI MVP funcional (3 rodadas, votação simples)
- [ ] 1 problema resolvido com consenso >= 75%
- [ ] Código Pydantic + motor básico comitado

### Médio Prazo (2 semanas)
- [ ] SACI completo (5 rodadas, convergência semântica)
- [ ] Problema da fábrica resolvido via SACI
- [ ] UI Streamlit para monitoramento

### Longo Prazo (1 mês)
- [ ] SACI em produção como serviço
- [ ] 10+ problemas resolvidos com sucesso
- [ ] Open-source release (GitHub)

---

**FIM DA ESPECIFICAÇÃO SACI v1.0**

*Baseado em consenso de: Gemini 2.5 PRO, GPT-5 CODEX, Grok 4, Claude 3.5 Sonnet*  
*Data: 2025-10-23*
