from pathlib import Path

path = Path('run.py')
text = path.read_text()
old = "        system = (\n            \"VocA� Ac um engenheiro de software responsA�vel por corrigir erros de sintaxe em arquivos Python.\"\n        )\n        user = (\n            f\"Arquivo: {rel_path}\\n\"\n            f\"Erro reportado pelo compilador Python:\\n{message}\\n\\n\"\n            \"ConteA�do atual do arquivo:\\n\"\n            \"`python\\n\"\n            f\"{content}\\n\"\n            \"`\\n\\n\"\n            \"Corrija o arquivo e devolva o conteA�do completo dentro de um bloco `python. \"\n            \"NA�o adicione comentA�rios extras ou explicaA�es, apenas o arquivo corrigido.\"\n        )\n"
new = "        system = (\n            \"You are a senior software engineer responsible for fixing Python syntax errors in place.\"\n        )\n        user = (\n            f\"File: {rel_path}\\n\"\n            f\"Compiler error:\\n{message}\\n\\n\"\n            \"Current file contents:\\n`python\\n\"\n            f\"{content}\\n\"\n            \"`\\n\\n\"\n            \"Return the corrected file enclosed in `python` with no extra commentary.\"\n        )\n"
if old not in text:
    raise SystemExit('old string not found')
path.write_text(text.replace(old, new))
