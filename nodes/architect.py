from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from llm_client import safe_json_extract
from router import Router
from tools.scaffolder import FLASHSOFT_ARCHITECT_SCHEMA, scaffold_from_plan
from utils.json_validation import SchemaValidationError, validate_plan
from validator_rules.requirements import enforce_plan_requirements


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_decomposer_prompt() -> tuple[str, str]:
    prompt_path = Path("prompts/task_decomposer.md")
    if not prompt_path.exists():
        return "", ""
    text = _read_text(prompt_path)
    prompt_section = text
    checklist = ""
    if "## Checklist" in text:
        prompt_section, checklist = text.split("## Checklist", 1)
    prompt_section = prompt_section.replace("## Prompt", "").strip()
    checklist = checklist.strip()
    return prompt_section, checklist


def run_task_decomposer(router: Router, spec_path: str) -> Optional[Dict[str, Any]]:
    """
    Use the TaskDecomposer prompt to break the SPEC into granular subtasks.
    Returns the JSON payload (with `tasks`) or None if the model output is unusable.
    """
    prompt_body, checklist = _load_decomposer_prompt()
    if not prompt_body:
        return None

    spec_text = Path(spec_path).read_text(encoding="utf-8")
    system_prompt = prompt_body
    parts = ["SPEC YAML:", spec_text.strip()]
    if checklist:
        parts.append("Checklist de validacao:")
        parts.append(checklist)
    parts.append("Responda estritamente com JSON valido contendo a chave 'tasks'.")
    user_prompt = "\n\n".join(parts)

    try:
        response = router.call(
            "decomposer",
            system_prompt,
            user_prompt,
            max_completion=2500,
            force_json=True,
        )
        data = safe_json_extract(response)
        tasks = data.get("tasks")
        if not isinstance(tasks, list):
            raise ValueError("Campo 'tasks' ausente ou invalido.")
        return {"tasks": tasks}
    except Exception:
        return None


def _load_architect_prompt() -> str:
    prompt_path = Path("prompts/architect.md")
    if not prompt_path.exists():
        raise FileNotFoundError("Prompts/architect.md nao encontrado.")
    schema_json = json.dumps(FLASHSOFT_ARCHITECT_SCHEMA, ensure_ascii=False, indent=2)
    return _read_text(prompt_path).replace("{{SCHEMA_JSON}}", schema_json)


def run_architect(
    router: Router,
    spec_path: str,
    repo_path: str,
    task_plan: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Produce an architect plan from the SPEC, validate it against the official schema,
    materialise the artifacts JSON file, and scaffold the repo.
    """
    spec_text = Path(spec_path).read_text(encoding="utf-8")
    system_prompt = _load_architect_prompt()

    user_sections = ["SPEC YAML:", spec_text.strip()]
    if task_plan:
        tasks_json = json.dumps(task_plan, ensure_ascii=False, indent=2)
        user_sections.append("TaskDecomposer JSON:")
        user_sections.append(tasks_json)
    user_sections.append("Responda somente com JSON valido de acordo com o schema fornecido.")
    user_prompt = "\n\n".join(user_sections)

    response = router.call(
        "architect",
        system_prompt,
        user_prompt,
        max_completion=6000,
        force_json=True,
    )
    raw_plan = safe_json_extract(response)
    try:
        validated_plan = validate_plan(raw_plan, FLASHSOFT_ARCHITECT_SCHEMA)
    except SchemaValidationError as exc:
        raise RuntimeError(f"Plano do Architect invalido: {exc}") from exc

    enforce_plan_requirements(validated_plan)

    repo = Path(repo_path)
    artifacts_dir = repo / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    plan_path = artifacts_dir / "architect_plan.json"
    plan_path.write_text(json.dumps(validated_plan, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = scaffold_from_plan(validated_plan, repo)

    return {
        "plan": validated_plan,
        "plan_path": plan_path,
        "scaffold_summary": summary,
    }
