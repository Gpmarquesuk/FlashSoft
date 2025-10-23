# FlashSoft

Autonomous software factory **Spec -> Code -> Tests -> PR** with multi-model agents, guardrails, and observability.

## Objective
See docs/OBJECTIVE.md for the mission, scope, SLOs, and roadmap milestones.

## Multi-model committee routing

### Factory stages

Pipeline order: Planner -> Implementer -> Tester -> Functional QA -> Reviewer -> Release. The QA stage runs the generated CLI end-to-end, verifies artifacts, writes `QA_REPORT.md`, and only then allows the release manager model to assemble the PR body.

Each node (planner, tester, reviewer, PR integrator) can run with a committee of specialists. Configure them via environment variables:
- GPT-5 Thinker supervises between attempts, choosing actions like `force_json` or `switch_planner` via structured JSON guidance.

MODEL_PLANNER=anthropic/claude-sonnet-4.5
MODEL_PLANNER_COMMITTEE=google/gemini-2.5-pro
MODEL_FALLBACK_PLANNER=google/gemini-2.5-pro

During execution the router logs every attempt (event router_model_attempt) and automatically pivots to the next model if one fails or returns invalid output. The successful specialist becomes the new primary model for subsequent calls, giving you automatic unsticking when a model stalls.

### Free profile for local development

Set `USE_FREE_MODELS=1` (or export it in the shell) to force the router to swap every node to free-tier models. You can also override each role explicitly:

```
MODEL_PLANNER_FREE=deepseek/deepseek-chat-v3.1:free
MODEL_FALLBACK_PLANNER_FREE=qwen/qwen-2.5-coder-32b-instruct:free
```

When `USE_FREE_MODELS=1` the router logs `profile=free` in the `router_committee` event so you can confirm tests are running without billing premium models.

## Example workflow

1. Drop a spec (e.g., examples/specs/interview_assistant.yaml) that describes the desired behaviour.
2. Run the orchestrator: .\run_spec.ps1 -Spec .\examples\specs\interview_assistant.yaml.
3. Watch the logs in logs/ for committee decisions, auto-dependency installs, functional QA status, and PR links.
4. GitHub Actions (.github/workflows/ci.yml) replays the tests on Ubuntu and reports back on the PR.

## Local MVP (Interview Assistant)

1. Configure `OPENROUTER_API_KEY` no `.env`.
2. Instale dependências e dados de exemplo:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python examples\prepare_sample_docs.py  # cria example resume/JD (opcional; use seus próprios arquivos PDF/DOCX)
   ```
3. Execute o assistente (modo headless para testes automatizados):
   ```powershell
   python -m src.interview_assistant `
     --resume examples/data/resume.pdf `
     --jd examples/data/job_description.docx `
     --question "Quais são seus diferenciais para esta vaga?" `
     --output-dir artifacts/mvp `
     --logs-dir logs/mvp `
     --no-audio `
     --headless-overlay
   ```
   - Para testar em tempo real com áudio use WASAPI: remova `--no-audio`.
   - Para abrir o overlay de UI remova `--headless-overlay` (ele aparece topmost e responde aos hotkeys: `Ctrl+Alt+Space` esconde/mostra, `Ctrl+Alt+Enter` marca como respondido).
4. Resultados:
   - `artifacts/mvp/last_answer.json`
   - `artifacts/mvp/overlay.html`
   - `logs/mvp/live_transcript.jsonl` (chunks transcritos)
   - `factory_state/` registra manifestos das execuções aprovadas (hash SHA256 + zip gerado em `dist/`).

### Observações sobre STT e interface

- A primeira execução do STT local (`faster-whisper`) baixa o modelo `base` (~140 MB).
- A interface interativa pode ser aberta com `python -m src.interview_assistant --ui` (permite escolher currículo, JD e WAV).
- Para simular o áudio da entrevista use `--audio-file caminho\para\entrevista.wav --auto-from-audio`; remova `--no-audio` para capturar via WASAPI em tempo real.
- O overlay HTML fica em `artifacts/overlay.html`; ao habilitar GUI ele aparece sempre em primeiro plano (hotkeys: `Ctrl+Alt+Space` alterna visibilidade, `Ctrl+Alt+Enter` marca como respondida).

## Development

- Activate the virtualenv: .\.venv\Scripts\Activate.ps1
- Install dependencies: pip install -r requirements.txt
- Run tests (free profile): `USE_FREE_MODELS=1 pytest`
