from pathlib import Path

path = Path('run.py')
text = path.read_text()
old = '''        system = (
            "Você é um engenheiro de software responsável por corrigir erros de sintaxe em arquivos Python."
        )
        user = (
            f"Arquivo: {rel_path}\\n"
            f"Erro reportado pelo compilador Python:\\n{message}\\n\\n"
            "Conteúdo atual do arquivo:\\n"
            "`python\\n"
            f"{content}\\n"
            "`\\n\\n"
            "Corrija o arquivo e devolva o conteúdo completo dentro de um bloco `python. "
            "Não adicione comentários extras ou explicações, apenas o arquivo corrigido."
        )'''
new = '''        system = (
            "You are a senior software engineer responsible for fixing Python syntax errors in place."
        )
        user = (
            f"File: {rel_path}\\n"
            f"Compiler error:\\n{message}\\n\\n"
            "Current file contents:\\n`python\\n"
            f"{content}\\n"
            "`\\n\\n"
            "Return the corrected file enclosed in `python` with no extra commentary."
        )'''
if old not in text:
    raise SystemExit('old block not found')
path.write_text(text.replace(old, new))
