# FlashSoft — Objetivo do Produto

**Missão:** Transformar uma *spec* em **PR** aprovado, sem intervenção humana, via um sistema **multi-agente** com **roteamento multi-modelo** (usar o melhor LLM por tarefa), guardrails, observabilidade e controle de orçamento.

**Escopo funcional (Spec → Código → Testes → PR):**
1. **Planner/Architect**: decompõe a spec em plano e arquitetura.
2. **Implementer**: gera/edita código e migrações.
3. **Tester**: cria/roda testes; só avança se passar.
4. **Reviewer**: revisão adversarial + segurança/licenças.
5. **PR Integrator**: abre PR com changelog, diffs, riscos e próximos passos.

**SLOs (medidos por execução):**
- **Qualidade**: ≥ X% dos PRs *merged* sem edição humana; regressões ≤ Y/100 PRs.
- **Velocidade**: lead time Spec→PR ≤ Z min (p95).
- **Custo**: TCO/PR ≤ $K (tokens + CI + infra).

**Diferenciais (moat):**
- **Roteador aprendente** (cost × qualidade × latência) por tarefa.
- **Comitê de modelos** e *judge* estruturado quando há incerteza.
- **Event sourcing**: traces completos para *replay*, auditoria e auto-evals.
- **Fallbacks** (free/on-prem) e *budget governor*.

**Não-objetivos (por enquanto):**
- Suporte a linguagens exóticas fora do SDK base.
- Ações que exigem credenciais de produção do usuário sem BYO-Keys.

**Roadmap resumido:**
- v0: E2E estável + métricas.
- v1: Router v0.1 (bandit) + auto-evals.
- v2: Comitê adaptativo + UI de *replay*.
