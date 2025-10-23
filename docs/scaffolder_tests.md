## Tests
```python
# tests/test_scaffolder.py
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence

import pytest

import tools.scaffolder as scaffolder


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_plan(files: Sequence[dict] | None = None) -> dict:
    file_entries = list(files) if files is not None else [
        {
            "path": "src/core/__init__.py",
            "description": "Package initialization for core.",
            "type": "code",
        },
        {
            "path": "src/core/service.py",
            "description": "Core service module implementation.",
            "type": "code",
        },
    ]
    return {
        "metadata": {
            "spec": "flashsoft-core-service",
            "created_at": _iso_now(),
            "architect": "Test Architect",
        },
        "components": [
            {
                "id": "core_service",
                "description": "Provides the core service scaffolding.",
                "responsibilities": ["Ensure service code is scaffolded correctly."],
                "dependencies": [],
                "files": file_entries,
                "acceptance_tests": [
                    {
                        "id": "core_service_acceptance",
                        "description": "Validate scaffold output.",
                        "success_criteria": "Generated files exist with expected stubs.",
                    }
                ],
            }
        ],
    }


def _locate_scaffolder_callable():
    candidate_funcs: List = []
    for name, func in inspect.getmembers(scaffolder, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        signature = inspect.signature(func)
        param_names = [param_name.lower() for param_name in signature.parameters]
        if not param_names:
            continue
        if any("plan" in param_name for param_name in param_names):
            candidate_funcs.append(func)
    if candidate_funcs:
        candidate_funcs.sort(
            key=lambda fn: (
                "scaffold" not in fn.__name__.lower(),
                len(inspect.signature(fn).parameters),
            )
        )
        return candidate_funcs[0]

    for name, attr in inspect.getmembers(scaffolder):
        if name.startswith("_"):
            continue
        if inspect.isclass(attr):
            if "scaffold" not in name.lower():
                continue
            try:
                instance = attr()
            except TypeError:
                continue
            for method_name in ("run", "execute", "apply", "scaffold", "__call__"):
                if hasattr(instance, method_name):
                    method = getattr(instance, method_name)
                    if callable(method):
                        return method
        elif callable(attr) and "scaffold" in name.lower():
            return attr

    raise RuntimeError("Unable to locate scaffolding entry point in tools.scaffolder")


def _invoke_scaffolder(plan_dict: dict, plan_file: Path, destination: Path):
    func = _locate_scaffolder_callable()
    signature = inspect.signature(func)

    positional_args = []
    keyword_args = {}

    for name, param in signature.parameters.items():
        lname = name.lower()
        value = None

        if "plan" in lname and "path" in lname:
            value = plan_file
        elif "plan" in lname:
            value = plan_dict
        elif any(
            key in lname
            for key in ("output", "dest", "directory", "dir", "root", "base", "target")
        ):
            value = destination
        elif "skip" in lname:
            value = True
        elif "overwrite" in lname:
            value = False
        elif "dry_run" in lname:
            value = False
        elif param.default is inspect._empty and param.kind == param.KEYWORD_ONLY:
            value = destination

        if value is None:
            continue

        if param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            positional_args.append(value)
        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
            keyword_args[name] = value

    try:
        return func(*positional_args, **keyword_args)
    except TypeError:
        positional_args = []
        keyword_args = {}
        for name, param in signature.parameters.items():
            lname = name.lower()
            value = None
            if "plan" in lname:
                value = plan_file
            elif any(
                key in lname
                for key in ("output", "dest", "directory", "dir", "root", "base", "target")
            ):
                value = destination
            elif "skip" in lname:
                value = True
            elif "overwrite" in lname:
                value = False
            elif "dry_run" in lname:
                value = False

            if value is None:
                continue

            if param.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ):
                positional_args.append(value)
            elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                keyword_args[name] = value
        return func(*positional_args, **keyword_args)


def _run_scaffolder(plan_dict: dict, tmp_path: Path, workspace: Path | None = None):
    plan_file = tmp_path / "architect_plan.json"
    plan_file.write_text(json.dumps(plan_dict, indent=2))
    workspace_dir = workspace or (tmp_path / "workspace")
    workspace_dir.mkdir(parents=True, exist_ok=True)
    result = _invoke_scaffolder(plan_dict, plan_file, workspace_dir)
    return result, workspace_dir


def _extract_paths_from_result(result, field: str) -> List[Path]:
    if result is None:
        return []
    candidates: Iterable = []
    if isinstance(result, dict):
        for key in (field, f"{field}_files", f"{field}_paths", f"{field}_items"):
            if key in result:
                candidates = result[key]
                break
    if not candidates and hasattr(result, field):
        candidates = getattr(result, field)
    if not candidates:
        alt_attr = f"{field}_files"
        if hasattr(result, alt_attr):
            candidates = getattr(result, alt_attr)
    if not candidates and isinstance(result, (list, tuple)):
        if field == "created" and len(result) >= 1:
            candidates = result[0]
        elif field == "skipped" and len(result) >= 2:
            candidates = result[1]

    if candidates is None:
        return []

    if not isinstance(candidates, (list, tuple, set)):
        candidates = [candidates]

    normalized = []
    for entry in candidates:
        if isinstance(entry, dict) and "path" in entry:
            entry = entry["path"]
        elif hasattr(entry, "path"):
            entry = getattr(entry, "path")
        path_obj = Path(entry) if not isinstance(entry, Path) else entry
        normalized.append(path_obj)
    return normalized


def _normalize_relative_paths(paths: Iterable[Path], base_dir: Path) -> set[str]:
    normalized = set()
    for path in paths:
        path_obj = Path(path)
        try:
            normalized.add(str(path_obj.relative_to(base_dir)))
        except ValueError:
            normalized.add(str(path_obj))
    return normalized


def test_invalid_plan_raises(tmp_path: Path):
    invalid_plan = {
        "metadata": {
            "spec": "invalid-plan",
            "created_at": _iso_now(),
            "architect": "QA Engineer",
        }
        # Missing "components"
    }

    with pytest.raises(Exception):
        _run_scaffolder(invalid_plan, tmp_path)


def test_scaffold_creates_directories_and_files(tmp_path: Path):
    plan = _make_plan()
    _, workspace = _run_scaffolder(plan, tmp_path)

    expected_dir = workspace / "src" / "core"
    assert expected_dir.is_dir(), "Expected component directory was not created."

    for relative in ("src/core/__init__.py", "src/core/service.py"):
        target = workspace / relative
        assert target.is_file(), f"Expected scaffolded file '{relative}' to be created."


def test_generated_python_file_contains_docstring_and_stub(tmp_path: Path):
    plan = _make_plan()
    _, workspace = _run_scaffolder(plan, tmp_path)

    py_file = workspace / "src" / "core" / "service.py"
    content = py_file.read_text()

    assert '"""' in content, "Generated Python file should include a module docstring."
    assert "Core service module implementation." in content, "Docstring should reflect file description."
    assert any(
        token in content for token in ("pass", "...", "raise NotImplementedError")
    ), "Generated Python file should include a stub implementation."


def test_existing_files_are_reported_as_skipped(tmp_path: Path):
    plan = _make_plan()
    workspace = tmp_path / "workspace"
    existing_file = workspace / "src" / "core" / "service.py"
    existing_file.parent.mkdir(parents=True, exist_ok=True)
    original_content = "do not overwrite"
    existing_file.write_text(original_content)

    result, _ = _run_scaffolder(plan, tmp_path, workspace=workspace)

    assert existing_file.read_text() == original_content, "Existing file should not be overwritten."

    skipped_paths = _extract_paths_from_result(result, "skipped")
    normalized = _normalize_relative_paths(skipped_paths, workspace)
    assert "src/core/service.py" in normalized, "Existing file should be reported as skipped."
```