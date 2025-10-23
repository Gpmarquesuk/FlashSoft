import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[0]
sys.path.append(str(SCRIPT_DIR))

from openrouter_client import call_model

def run():
    schema_text = Path(ROOT / 'docs/architect_spec.md').read_text(encoding='utf-8')
    prompt = f"""
Você é GPT-5 Codex atuando como engenheiro de ferramentas.
Temos o artefato do Architect abaixo (schema + exemplo):

{schema_text}

Preciso apenas do código Python completo do módulo `tools/scaffolder.py` que:
1. Valide o plano contra o schema usando `jsonschema`.
2. Crie diretórios e arquivos conforme o plano.
3. Gere conteúdo para arquivos `.py` com docstring e stubs baseados em `responsibilities`.
4. Registrar logs simples e devolver um resumo `dict`.

Requisitos:
- Sem testes, apenas o módulo.
- Responder com um único bloco ```python contendo o código.
- Código auto-contido, usando pathlib, json, logging.
"""

    messages = [
        {"role": "system", "content": "Você escreve módulos Python robustos para pipelines multiagente."},
        {"role": "user", "content": prompt},
    ]

    response = call_model("openai/gpt-5-codex", messages, max_tokens=2000, temperature=0.0)
    Path(ROOT / 'docs/scaffolder_module.md').write_text(response, encoding='utf-8')
    print('Código do scaffolder salvo em docs/scaffolder_module.md')

if __name__ == '__main__':
    run()
