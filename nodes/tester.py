import json
from router import Router
from llm_client import safe_json_extract

def run_tester(router: Router, patches: list, test_plan: str) -> dict:
    files = [p["path"] for p in patches]
    with open("prompts/tester.md", "r", encoding="utf-8") as f:
        system = f.read()
    user = f"""Arquivos a serem testados:
{json.dumps(files, ensure_ascii=False)}
Plano de testes:
{test_plan}
Responda somente com o JSON esperado.
"""
    out = router.call("tester", system, user, max_completion=2500)
    data = safe_json_extract(out)
    assert "patches" in data, "JSON invÃ¡lido do Tester"
    return data
