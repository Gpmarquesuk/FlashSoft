import json

from router import Router
from llm_client import safe_json_extract


def run_tester(router: Router, patches: list, test_plan: str) -> dict:
    files = [p["path"] for p in patches]
    with open("prompts/tester.md", "r", encoding="utf-8") as f:
        system = f.read()
    base_user = (
        "Arquivos a serem testados:\n"
        f"{json.dumps(files, ensure_ascii=False)}\n"
        "Plano de testes:\n"
        f"{test_plan}\n"
        "Responda somente com o JSON esperado."
    )
    last_error = ""
    for attempt in range(1, 4):
        user = base_user
        if last_error:
            user += (
                "\n\nATENCAO: a tentativa anterior nao pôde ser convertida em JSON. "
                f"Erro capturado: {last_error}. Responda apenas com JSON valido."
            )
        try:
            out = router.call("tester", system, user, max_completion=2000, force_json=True)
            data = safe_json_extract(out)
            assert "patches" in data, "JSON invalido do Tester"
            return data
        except Exception as exc:
            last_error = "".join(ch for ch in str(exc) if 31 < ord(ch) < 127)
            continue

    raise RuntimeError(f"Tester falhou apos 3 tentativas: {last_error or 'erro desconhecido'}")
