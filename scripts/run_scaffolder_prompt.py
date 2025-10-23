import json
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
Temos o seguinte artefato do agente Architect:

{schema_text}

Precisamos implementar um agente `Scaffolder` em Python que receba o JSON produzido pelo Architect e:
1. Valide contra o schema (use `jsonschema`).
2. Crie a árvore de diretórios conforme os `files` de cada componente.
3. Para cada arquivo, gerar conteúdo inicial:
   - Arquivos `.py` com cabeçalho, docstring derivada de `description` e, se `responsibilities` indicar classes/funções, gerar stubs com `raise NotImplementedError`.
   - Gerar `__init__.py` apropriados e evitar sobrescrever arquivos existentes sem permissão.
4. Registrar log simples para cada artefato criado.
5. Retornar um resumo (dict) com `created_files`, `skipped`, `errors`.

Além disso, produza testes unitários (`pytest`) cobrindo:
- Validação de schema (caso inválido).
- Geração de arquivo Python com stub e docstring.
- Criação de diretórios inexistentes.

Requisitos de saída:
- Responda com seções: `## Scaffolder`, `## Tests`.
- Cada seção deve conter um bloco ```python com o código completo.
- O código do Scaffolder deve ser auto-contido em módulo `tools/scaffolder.py` (assuma diretório).
- Os testes em `tests/test_scaffolder.py` assumindo estrutura pytest.
"""

    messages = [
        {"role": "system", "content": "Você escreve ferramentas Python robustas e testáveis."},
        {"role": "user", "content": prompt},
    ]

    response = call_model("openai/gpt-5-codex", messages, max_tokens=3000, temperature=0.0)
    Path(ROOT / 'docs/scaffolder_spec.md').write_text(response, encoding='utf-8')
    print('Tamanho resposta:', len(response))

if __name__ == '__main__':
    run()
