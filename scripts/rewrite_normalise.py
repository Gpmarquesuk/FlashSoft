from pathlib import Path

path = Path('run.py')
text = path.read_text()
needle = 'def _normalise_repo(repo_path: str) -> None:\n'
insertion = '''def _normalise_repo(repo_path: str) -> None:\n    repo = Path(repo_path)\n    legacy_pkg = repo / "src" / "interview"\n    target_pkg = repo / "src" / "interview_assistant"\n    if legacy_pkg.exists():\n        if target_pkg.exists():\n            shutil.rmtree(target_pkg)\n        shutil.move(str(legacy_pkg), str(target_pkg))\n        replacements = {\n            "from interview.": "from interview_assistant.",\n            "from interview import": "from interview_assistant import",\n            "from src.interview": "from src.interview_assistant",\n            "import interview.": "import interview_assistant.",\n            "import interview ": "import interview_assistant ",\n            "import interview\n": "import interview_assistant\n",\n            "import src.interview": "import src.interview_assistant",\n        }\n        for py_file in repo.rglob("*.py"):\n            text = py_file.read_text(encoding="utf-8")\n            new_text = text\n            for old, new in replacements.items():\n                new_text = new_text.replace(old, new)\n            if new_text != text:\n                py_file.write_text(new_text, encoding="utf-8")\n        init_path = target_pkg / "__init__.py"\n        init_path.write_text("from .assistant import *\\nInterviewAssistant = Assistant\\n", encoding="utf-8")\n\n\n'}'''
if needle not in text:
    raise SystemExit('needle changed')
# remove old function (current) first? For simplicity, assume first occurrence only and replace manually
start = text.index(needle)
end = text.index('\n\n\n\ndef _apply_baseline_solution', start)
text = text[:start] + insertion + text[end+1:]
# insert helper functions after _normalise_repo definition
helpers = '''def _extract_code_block(response: str) -> str | None:\n    fence = "`"\n    if fence not in response:\n        return None\n    parts = response.split(fence)\n    if len(parts) < 3:\n        return None\n    code = parts[1]\n    if code.startswith("python"):\n        code = code[len("python"): ]\n    return code.strip("\n")\n\n\ndef _fix_syntax_errors(router: Router, repo_path: str, errors: list[tuple[Path, str]]) -> bool:\n    if not errors:\n        return False\n    fixed_any = False\n    for abs_path, message in errors:\n        rel_path = abs_path.relative_to(repo_path)
        if not abs_path.exists():
            continue
        content = abs_path.read_text(encoding="utf-8")
        system = (
            "Você é um engenheiro de software responsável por corrigir erros de sintaxe em arquivos Python."
        )
        user = (
            f"Arquivo: {rel_path}\n"
            f"Erro reportado pelo compilador Python:\n{message}\n\n"
            "Conteúdo atual do arquivo:\n"
            "`python\n"
            f"{content}\n"
            "`\n\n"
            "Corrija o arquivo e devolva o conteúdo completo dentro de um bloco `python. "
            "Não adicione comentários extras ou explicações, apenas o arquivo corrigido."
        )
        try:
            response = router.call(
                "assistant",
                system,
                user,
                max_completion=1500,
                force_json=False,
            )
        except Exception:
            continue
        new_content = _extract_code_block(response)
        if not new_content:
            new_content = response.strip()
        if new_content and new_content != content:
            abs_path.write_text(new_content, encoding="utf-8")
            fixed_any = True
    return fixed_any


'''
text = text.replace(insertion, insertion + helpers)
path.write_text(text)
