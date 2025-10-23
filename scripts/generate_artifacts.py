import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[0]
sys.path.append(str(SCRIPT_DIR))

from openrouter_client import call_model

ARCHITECT_DOC = (ROOT / 'docs/architect_spec.md').read_text(encoding='utf-8')

MODEL = "openai/gpt-5-codex"
MAX_TOKENS = 200000  # prompt + completion limit (within 400k context)
MAX_OUTPUT = 120000  # below provider 128k cap

TASKS = {
    'scaffolder_module': {
        'path': ROOT / 'docs/scaffolder_module.md',
        'prompt': f"""
Você é GPT-5 Codex atuando como engenheiro de ferramentas.
Abaixo está o artefato do Architect (schema + exemplo):

{ARCHITECT_DOC}

Preciso do módulo completo `tools/scaffolder.py` com as seguintes características:
1. Validar o plano JSON contra o schema usando `jsonschema`.
2. Criar diretórios e arquivos indicados em `components[*].files`.
3. Para cada arquivo `.py`, gerar docstring derivada de `description` e stubs (classes/funções) baseadas nas `responsibilities` (parse simples: frases começando com 'Classe', 'Função', etc.). Use `raise NotImplementedError`.
4. Não sobrescrever arquivos existentes; registrar quando for pulado.
5. Retornar um resumo (`dict`) com `created_files`, `skipped_files`, `errors`.
6. Usar logging padrão (`logging`), pathlib e typing.

Saída: seção `## Scaffolder` com bloco ```python contendo o módulo completo.
""",
    },
    'scaffolder_tests': {
        'path': ROOT / 'docs/scaffolder_tests.md',
        'prompt': f"""
Você é GPT-5 Codex e deve escrever testes `pytest` para o módulo `tools/scaffolder.py` (ver artefato do Architect abaixo):

{ARCHITECT_DOC}

Os testes devem cobrir:
- JSON inválido (schema) lança exceção.
- Criação de diretórios/arquivos (tmp_path).
- Geração de arquivo `.py` com docstring e stub.
- `skipped_files` quando arquivo já existe.

Responda com `## Tests` + bloco ```python para `tests/test_scaffolder.py`.
""",
    },
    'json_validator': {
        'path': ROOT / 'docs/json_validation_helpers.md',
        'prompt': """
Atue como especialista em validação. Escreva utilitários Python (`utils/json_validation.py`) que:
1. Carregam o JSON schema do Architect (aceitar string ou Path).
2. Validam o plano com `jsonschema` (Draft7), retornando dados normalizados.
3. Propaguem erros informativos.
Inclua testes pytest correspondentes.
Responda com `## JSON Utils` (```python) e `## JSON Tests` (```python).
""",
    },
    'task_decomposer': {
        'path': ROOT / 'docs/task_decomposer_prompt.md',
        'prompt': """
Você é GPT-5 Codex e deve escrever o prompt e guidelines para um agente `TaskDecomposer` que, dado um SPEC, devolve sub-tarefas pequenas conforme o schema do Architect. Produza:
- `## Prompt` com texto pronto.
- `## Checklist` enumerando critérios (granularidade, dependências, nomes consistentes, etc.).
""",
    },
}

SYSTEM_MESSAGE = (
    "Você é um consultor técnico trabalhando para a fábrica FlashSoft. "
    "Entregue código completo exatamente no formato solicitado."
)


def run_task(name: str, info: dict) -> tuple[str, str]:
    messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": info['prompt']},
    ]
    content = call_model(
        MODEL,
        messages,
        max_tokens=MAX_TOKENS,
        max_output_tokens=MAX_OUTPUT,
        temperature=0.0,
    )
    info['path'].write_text(content, encoding='utf-8')
    return name, f"Salvo em {info['path'].relative_to(ROOT)} (len={len(content)})"


def main():
    with ThreadPoolExecutor(max_workers=len(TASKS)) as executor:
        futures = {executor.submit(run_task, name, info): name for name, info in TASKS.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                result_name, message = future.result()
                print(f"[{result_name}] {message}")
            except Exception as exc:
                print(f"[{name}] ERRO: {exc}")

if __name__ == '__main__':
    main()
