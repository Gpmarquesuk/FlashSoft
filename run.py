# -*- coding: utf-8 -*-
import argparse
import json
import os
import subprocess
import sys
import uuid
import hashlib
import zipfile
from pathlib import Path
from typing import Iterable, List, Tuple

from dotenv import load_dotenv

load_dotenv()

from state import RunState
from router import Router
from github_integration import clone_repo, create_branch, commit_push, open_pr
from patcher import apply_patches, write_review
from nodes.architect import run_architect, run_task_decomposer
from nodes.integrator import run_integrator
from nodes.planner_coder import run_planner_coder
from nodes.tester import run_tester
from nodes.reviewer import run_reviewer
from nodes.pr_integrator import run_pr_integrator
from nodes.qa_specialist import FunctionalQAFailed, run_functional_qa
from validators import check_syntax
from utils import new_run_id
from utils.repo import normalise_interview_package
from factory_state import FactoryState, ReleaseRecord


def _extract_code_block(response: str) -> str | None:
    """
    Extract the first fenced code block from the model response.
    """
    fence = "```"
    if fence not in response:
        return None
    parts = response.split(fence)
    if len(parts) < 3:
        return None
    code = parts[1]
    if code.startswith("python"):
        code = code[len("python") :]
    return code.strip("\n")


def _fix_syntax_errors(
    router: Router, repo_path: str, errors: List[Tuple[Path, str]]
) -> bool:
    """
    Ask the assistant model to fix syntax errors and rewrite the files.
    Returns True if at least one file was modified.
    """
    fixed_any = False
    for abs_path, message in errors:
        if not abs_path.exists():
            continue
        rel_path = abs_path.relative_to(repo_path)
        content = abs_path.read_text(encoding="utf-8")
        system = (
            "You are a senior software engineer responsible for fixing Python syntax errors in place."
        )
        user = (
            f"File: {rel_path}\n"
            f"Compiler error:\n{message}\n\n"
            "Current file contents:\n```python\n"
            f"{content}\n"
            "```\n\n"
            "Return the corrected file enclosed in `python` with no extra commentary."
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


def _run_syntax_guard(router: Router, repo_path: str, relative_paths: Iterable[Path]) -> None:
    python_files = [Path(repo_path) / path for path in relative_paths if path.suffix == ".py"]
    if not python_files:
        return
    errors = check_syntax(python_files)
    if not errors:
        return
    fixed = _fix_syntax_errors(router, repo_path, errors)
    if fixed:
        errors = check_syntax(python_files)
    if errors:
        details = "\n".join(f"{path.relative_to(repo_path)}: {msg}" for path, msg in errors)
        raise RuntimeError(f"Syntax errors persist after auto-fix:\n{details}")


def _apply_baseline_solution(repo_path: str) -> None:
    raise RuntimeError(
        "Legacy baseline fallback removed. Use nodes.integrator.run_integrator instead."
    )
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, help="caminho para spec.yaml")

def _create_release_bundle(repo_path: str, run_id: str, branch: str) -> ReleaseRecord:
    repo = Path(repo_path)
    dist_dir = repo / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    output_dir = repo / "artifacts"
    logs_dir = repo / "logs"
    package_name = f"autobot_{run_id}.zip"
    package_path = dist_dir / package_name

    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        if output_dir.exists():
            for item in sorted(output_dir.rglob("*")):
                if item.is_file():
                    arcname = Path("artifacts") / item.relative_to(output_dir)
                    bundle.write(item, arcname)
        if logs_dir.exists():
            for item in sorted(logs_dir.rglob("*")):
                if item.is_file():
                    arcname = Path("logs") / item.relative_to(logs_dir)
                    bundle.write(item, arcname)

    sha256 = hashlib.sha256(package_path.read_bytes()).hexdigest()
    record = ReleaseRecord(
        run_id=run_id,
        branch=branch,
        package=str(package_path.relative_to(repo)),
        sha256=sha256,
        tests=["pytest -q", "functional_qa"],
        release_tag=f"staging-{run_id}",
        release_asset=package_name,
    )

    state = FactoryState(repo)
    state.record_release(record)
    return record
    parser.add_argument("--branch", default=None, help="nome da branch a criar")
    args = parser.parse_args()

    run_id = new_run_id()
    state = RunState(run_id)
    router = Router(event_logger=state.log)
    state.log(
        {
            "event": "router_models",
            "models": router.models,
            "fallbacks": router.fallbacks,
            "committees": router.committee_snapshot(),
        }
    )

    workdir = os.getenv("WORKDIR", "/tmp/autobot_work")
    os.makedirs(workdir, exist_ok=True)
    repo_path = clone_repo(workdir)
    branch = args.branch or f"autobot/{run_id}"
    create_branch(repo_path, branch)

    state.log({"event": "start", "run_id": run_id, "branch": branch})

    normalise_interview_package(repo_path)

    task_plan = run_task_decomposer(router, args.spec)
    tasks_path: Path | None = None
    if task_plan:
        artifacts_dir = Path(repo_path) / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        tasks_path = artifacts_dir / "task_breakdown.json"
        tasks_path.write_text(json.dumps(task_plan, ensure_ascii=False, indent=2), encoding="utf-8")
        state.log(
            {
                "event": "task_decomposer_done",
                "tasks_path": str(tasks_path.relative_to(repo_path)),
                "task_count": len(task_plan.get("tasks", [])),
            }
        )

    architect_output = run_architect(router, args.spec, repo_path, task_plan)
    scaffold_summary = architect_output["scaffold_summary"]
    created_files = scaffold_summary.get("created_files", [])
    skipped_files = scaffold_summary.get("skipped_files", [])
    errors = scaffold_summary.get("errors", [])
    state.log(
        {
            "event": "architect_done",
            "plan_path": str(architect_output["plan_path"].relative_to(repo_path)),
            "created_count": len(created_files),
            "skipped_count": len(skipped_files),
            "error_count": len(errors),
            "created_sample": created_files[:5],
            "skipped_sample": skipped_files[:5],
            "errors_sample": errors[:3],
        }
    )

    normalise_interview_package(repo_path)

    data = run_planner_coder(router, repo_path, args.spec, task_plan=task_plan)
    patches = data["patches"]
    test_plan = data["test_plan"]
    state.log({"event": "planner_coder_done", "patch_count": len(patches)})

    apply_patches(repo_path, patches)
    planner_changed = {Path(p['path']) for p in patches if p.get('op', 'upsert') != 'delete'}
    normalise_interview_package(repo_path)
    _run_syntax_guard(router, repo_path, planner_changed)

    tests = run_tester(router, patches, test_plan)
    test_patches = tests["patches"]
    apply_patches(repo_path, test_patches)
    tester_changed = {Path(p['path']) for p in test_patches if p.get('op', 'upsert') != 'delete'}
    normalise_interview_package(repo_path)
    _run_syntax_guard(router, repo_path, tester_changed)
    state.log({"event": "tester_done", "test_patch_count": len(test_patches)})

    integrator_result = run_integrator(repo_path)
    state.log(
        {
            "event": "integrator_result",
            "pytest_ok": integrator_result["pytest_ok"],
            "missing_modules": integrator_result["missing_modules"],
            "dependencies_installed": integrator_result["dependencies_installed"],
            "dependencies_declared": integrator_result["dependencies_declared"],
            "baseline_applied": integrator_result["baseline_applied"],
            "pytest_output": integrator_result["pytest_output"],
        }
    )
    if not integrator_result["pytest_ok"]:
        raise RuntimeError("Pytest failed after dependency remediation.")

    try:
        qa_result = run_functional_qa(router, repo_path)
    except FunctionalQAFailed as exc:
        state.log({"event": "functional_qa_failed", "message": str(exc)})
        raise
    else:
        state.log(
            {
                "event": "functional_qa_done",
                "report_path": str(qa_result.report_path.relative_to(repo_path)),
                "overlay_path": str(qa_result.overlay_path.relative_to(repo_path)),
                "artifact_path": str(qa_result.artifact_path.relative_to(repo_path)),
                "transcript_path": str(qa_result.transcript_path.relative_to(repo_path)),
            }
        )

    release_record = _create_release_bundle(repo_path, run_id, branch)
    state.log({"event": "release_bundle_created", **release_record.to_dict()})

    commit_push(repo_path, f"[autobot] apply patches and tests - {run_id}", branch)

    review_md = run_reviewer(router, repo_path, context="MVP 4 nA3s")
    write_review(repo_path, review_md)
    commit_push(repo_path, f"[autobot] add REVIEW.md - {run_id}", branch)
    state.log({"event": "reviewer_done"})

    metadata = {
        "run_id": run_id,
        "dependencies_installed": integrator_result["dependencies_installed"],
        "dependencies_declared": integrator_result["dependencies_declared"],
        "baseline_applied": integrator_result["baseline_applied"],
        "qa_report": str(qa_result.report_path.relative_to(repo_path)),
        "qa_overlay": str(qa_result.overlay_path.relative_to(repo_path)),
        "release_package": release_record.package,
        "release_sha256": release_record.sha256,
        "release_tag": release_record.release_tag,
        "release_asset": release_record.release_asset,
        "release_manifest": f"factory_state/releases/{run_id}.json",
    }
    if tasks_path:
        metadata["task_breakdown"] = str(tasks_path.relative_to(repo_path))
    metadata["architect_plan"] = str(architect_output["plan_path"].relative_to(repo_path))
    pr_body = run_pr_integrator(
        router,
        pr_title=f"Autobot PR {run_id}",
        default_body=review_md,
        metadata=metadata,
    )
    pr_number = open_pr(branch, f"Autobot PR {run_id}", pr_body)
    state.log({"event": "pr_opened", "pr_number": pr_number})
    state.log({"event": "router_metrics", **router.metrics()})
    print(f"PR aberto: #{pr_number}")


if __name__ == "__main__":
    main()
