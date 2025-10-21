# FlashSoft — Objetivo do Produto

**Missão:** Transformar uma *spec* em **PR** aprovado, sem intervenção humana, via sistema **multi-agente** com **roteamento multi-modelo**, guardrails, observabilidade e controle de orçamento.

**Fluxo (Spec → Código → Testes → PR):**
1. Planner/Architect — decompõe a spec em plano e arquitetura.
2. Implementer — gera/edita código.
3. Tester — cria/roda testes; só avança se passar.
4. Reviewer — revisão adversarial + segurança/licenças.
5. PR Integrator — abre PR com changelog, diffs, riscos.

**SLOs:**
- Qualidade: % de PRs merged sem edição; regressões/100 PRs.
- Velocidade: lead time Spec→PR (p95).
- Custo: TCO/PR (tokens + CI + infra).

**Diferenciais:**
- Roteador aprendente (custo × qualidade × latência).
- Comitê de modelos + juiz estruturado.
- Event sourcing (traces) p/ replay, auditoria, auto-evals.
- Fallbacks (free/on-prem) e budget governor.

**Roadmap resumido:** v0 E2E estável + métricas → v1 router + auto-evals → v2 comitê adaptativo + UI de replay.
