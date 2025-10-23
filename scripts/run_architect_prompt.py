import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[0]
sys.path.append(str(SCRIPT_DIR))

from openrouter_client import call_model

PROMPT = """
Você é GPT-5 Codex atuando como arquiteto de pipelines multi-agente.

Contexto da fábrica FlashSoft:
- Queremos substituir o Planner por agentes especializados.
- O agente `Architect` recebe uma spec (ex.: STT com Whisper) e deve devolver um plano estruturado em JSON.
- Em seguida, o agente `Scaffolder` usará esse JSON para criar diretórios e arquivos vazios.

Sua tarefa agora é definir, com precisão:
1. O formato de saída do `Architect` como um JSON Schema Draft 7. Deve incluir campos como `metadata`, `components` (lista de objetos com id, description, responsibilities, dependencies, files, acceptance_tests) e opcionalmente `notes`.
2. Um exemplo de saída JSON válido usando o schema, para o caso "STT com Whisper live".
3. Uma lista de instruções numeradas para o prompt do agente `Architect`, garantindo que ele sempre siga o schema, valide, e explicite suposições.

Requisitos:
- Responda em Markdown com seções: `## JSON Schema`, `## Exemplo`, `## Instruções`.
- Schema em bloco ```json, exemplo também em ```json.
- Instruções como lista numerada, enfatizando verificar dependências, nomes de arquivos, granularidade.
"""

messages = [
    {"role": "system", "content": "Você é um consultor técnico escrevendo artefatos robustos para um pipeline multi-agente."},
    {"role": "user", "content": PROMPT},
]

response = call_model("openai/gpt-5-codex", messages, max_tokens=1500, temperature=0.1)
Path(ROOT / 'docs/architect_spec.md').write_text(response, encoding='utf-8')
print('Resposta do Architect gravada em docs/architect_spec.md')
