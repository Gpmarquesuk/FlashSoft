import json
from pathlib import Path

import yaml

from llm_client import safe_json_extract
from json_sanitizer import safe_json_extract_v2
from router import Router

TOKEN_THRESHOLD_SPEC = 500_000


def _clean_error_message(error: Exception) -> str:
    return ''.join(ch for ch in str(error) if 31 < ord(ch) < 127)


def run_planner_coder(
    router: Router,
    repo_path: str,
    spec_path: str,
    task_plan: dict | None = None,
) -> dict:
    with open(spec_path, 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    spec_dump = yaml.safe_dump(spec, sort_keys=False)
    approx_tokens = len(spec_dump) // 4
    if approx_tokens > TOKEN_THRESHOLD_SPEC:
        router.promote_model(
            'planner',
            router.fallbacks.get('planner'),
            reason=f'spec_tokens>{TOKEN_THRESHOLD_SPEC}',
        )

    file_list: list[str] = []
    for path in Path(repo_path).rglob('*.py'):
        rel = str(path.relative_to(repo_path))
        if rel.startswith('.venv') or rel.startswith('.git'):
            continue
        if len(file_list) > 60:
            break
        file_list.append(rel)

    with open('prompts/planner_coder.md', 'r', encoding='utf-8') as f:
        system = f.read()

    base_user_parts = [
        f"SPEC:\n{spec_dump}",
        f"REPO_FILES:\n{json.dumps(file_list, ensure_ascii=False, indent=2)}",
    ]
    if task_plan:
        base_user_parts.append(f"TASK_BREAKDOWN:\n{json.dumps(task_plan, ensure_ascii=False, indent=2)}")
    base_user_parts.append("Responda estritamente no JSON exigido.")
    base_user = "\n".join(base_user_parts)

    last_error = ''
    for attempt in range(10):  # Aumentado de 3 para 10 tentativas
        user = base_user
        if last_error:
            user += (
                '\n\nATENCAO: a tentativa anterior falhou ao interpretar o JSON. '
                f'Erro capturado: {last_error}. Garanta que a resposta esteja em JSON valido.'
            )
        try:
            out = router.call('planner', system, user, max_completion=3000, force_json=False)  # force_json=False para permitir markdown
            data = safe_json_extract_v2(out, expected_keys=['patches', 'test_plan'])  # Usa novo sanitizer
            assert 'patches' in data and 'test_plan' in data, 'JSON invalido do PlannerCoder'
            return data
        except Exception as exc:
            last_error = _clean_error_message(exc)
            committee = router.committee_snapshot().get('planner') or []
            if attempt + 1 < len(committee):
                next_model = committee[attempt + 1]
                router.promote_model('planner', next_model, reason='planner_json_error')

    raise RuntimeError(f'Planner falhou apos 10 tentativas: {last_error or "erro desconhecido"}')
