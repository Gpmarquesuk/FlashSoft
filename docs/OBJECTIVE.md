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

## Padrão Permanente de QA e UI

- **QA Specialist obrigatório**
  - Executa o CLI com os artefatos reais em `examples/manual_inputs/` (DOCX, PDF e WAV).
  - Reprova se `last_answer.json` tiver >45 palavras, se não gerar overlay ou se `logs/live_transcript.jsonl` estiver vazio.
  - Gera `QA_REPORT.md` anexado ao PR; Reviewer bloqueia merge sem esse relatório.

- **Pilar de testes de UI**
  - Playwright (componentes, integração e fluxos e2e) + axe-core para acessibilidade.
  - Vision AI (Claude/GPT-4o) para inspeção visual em 3 resoluções (1024×768, 1366×768, 1920×1080).
  - Baselines de screenshot versionadas (Percy/Chromatic); qualquer dif aplicado pelo pipeline exige aprovação manual.

- **Requisitos mínimos de UI**
  - Layout responsivo (painéis scrolláveis, sem clipping quando maximizado).
  - Hotkeys documentadas e ativas (`Alt+S`, `Alt+G`, `Alt+E`), labels ASCII.
  - Overlay com resposta ≤45 palavras e talking points ≤12 palavras, sempre em inglês.

- **Observabilidade**
  - Métricas: `latency_transcription_ms` (p95 <2s), `whisper_405_count`, `ui_hotkey_missing`.
  - Alertas em caso de regressão; auditoria semanal obrigatória do comitê de revisão.

Esses critérios valem para todo produto que a FlashSoft entregar, não apenas para o Interview Assistant.
