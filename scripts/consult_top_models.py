import json
import os
import textwrap
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get('OPENROUTER_API_KEY')
if not api_key:
    raise SystemExit('OPENROUTER_API_KEY not set')

HEADERS = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/GpmarquesUK/FlashSoft",
    "X-Title": "flashsoft-autobot-mvp",
}
MODELS = {
    "x-ai/grok-4": "Grok 4 Thinker",
    "google/gemini-2.5-pro": "Gemini 2.5 Pro",
    "anthropic/claude-sonnet-4.5": "Claude 4.5 Thinker",
}
USER_PROMPT = textwrap.dedent(
    """
    Somos a fábrica de software FlashSoft. Contexto atual:
    - O pipeline executa os nós Planner -> Tester -> QA -> Release usando modelos no OpenRouter.
    - Mesmo com modelos premium, Planner/Testador frequentemente retornam JSON inválido (vírgulas ausentes, strings truncadas), impedindo aplicar patches.
    - Quando os patches são aplicados, o código gerado costuma ter problemas estruturais (pacote errado, f-strings truncadas, testes chamando funções inexistentes) e os testes falham. O QA funcional nem chega a rodar.
    - Implementamos auto-reparo: repetimos a chamada até 3 vezes avisando o erro, normalizamos diretórios, instalamos dependências automaticamente, rodamos QA funcional e temos um supervisor (GPT-5) decidindo ações entre tentativas. Ainda assim, não convergimos para um MVP (por exemplo, módulo STT com Whisper live).

    Pergunta: qual estratégia robusta você recomenda para fazer a fábrica convergir para uma entrega completa a partir da spec? Considere ajustes de prompts, decomposição de tarefas, agentes auxiliares (checkers/fixers), verificações automáticas e coordenação entre nós. Liste passos concretos.
    """
)

results = {}
for model, label in MODELS.items():
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Você é um consultor sênior de engenharia de software, especialista em pipelines multiagente."},
            {"role": "user", "content": USER_PROMPT},
        ],
        "temperature": 0.2,
        "max_tokens": 2048,
        "max_output_tokens": 2048,
    }
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=HEADERS,
            json=payload,
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()
        results[label] = data["choices"][0]["message"]["content"].strip()
    except requests.HTTPError as err:
        msg = err.response.text if err.response is not None else str(err)
        results[label] = f"Falha HTTP {err.response.status_code if err.response else 'unknown'}: {msg}"
    except Exception as exc:
        results[label] = f"Erro: {exc}"

report = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "consultation": results,
}
Path("docs").mkdir(exist_ok=True)
Path("docs/consultation_top_models.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(json.dumps(report, ensure_ascii=False, indent=2))
