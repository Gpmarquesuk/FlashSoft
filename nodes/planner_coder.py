import yaml, json
from pathlib import Path
from router import Router
from llm_client import safe_json_extract

def run_planner_coder(router: Router, repo_path: str, spec_path: str) -> dict:
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    file_list = []
    for p in Path(repo_path).rglob("*.py"):
        rel = str(p.relative_to(repo_path))
        if rel.startswith(".venv") or rel.startswith(".git"):
            continue
        if len(file_list) > 60:
            break
        file_list.append(rel)

    with open("prompts/planner_coder.md", "r", encoding="utf-8") as f:
        system = f.read()

    user = f"""SPEC:
{yaml.safe_dump(spec, sort_keys=False)}
REPO_FILES:
{json.dumps(file_list, ensure_ascii=False, indent=2)}
Responda estritamente no JSON exigido."""
    # Força JSON nativo + parser tolerante
    out = router.call("planner", system, user, max_completion=3000, force_json=True)
    data = safe_json_extract(out)
    assert "patches" in data and "test_plan" in data, "JSON inválido do PlannerCoder"
    return data
