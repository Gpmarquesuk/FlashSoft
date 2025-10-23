import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from state import RunState
from router import Router
from github_integration import clone_repo, create_branch, commit_push, open_pr
from patcher import apply_patches, write_review
from nodes.planner_coder import run_planner_coder
from nodes.tester import run_tester
from nodes.reviewer import run_reviewer
from nodes.pr_integrator import run_pr_integrator
from nodes.qa_specialist import FunctionalQAFailed, run_functional_qa
from utils import new_run_id

MODULE_PACKAGE_OVERRIDES = {
    "yaml": "PyYAML",
    "pil": "Pillow",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "bs4": "beautifulsoup4",
}


def run_pytests(repo_path: str):
    try:
        env = os.environ.copy()
        env.setdefault("USE_FREE_MODELS", "1")
        out = subprocess.run(
            ["pytest", "-q"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        ok = out.returncode == 0
        return ok, out.stdout + "\n" + out.stderr
    except Exception as e:
        return False, str(e)


def _extract_missing_modules(output: str) -> set[str]:
    misses: set[str] = set()
    if not output:
        return misses
    markers = ["ModuleNotFoundError: No module named '", "ImportError: No module named '"]
    for line in output.splitlines():
        for marker in markers:
            if marker in line:
                start = line.find(marker) + len(marker)
                end = line.find("'", start)
                if end > start:
                    module = line[start:end].strip()
                    if module:
                        misses.add(module)
    return misses


def _map_module_to_package(module: str) -> str:
    key = module.lower()
    return MODULE_PACKAGE_OVERRIDES.get(key, module)


def _ensure_dependencies(
    repo_path: str, missing_modules: set[str]
) -> tuple[bool, list[str], list[str]]:
    if not missing_modules:
        return False, [], []

    requirements_path = Path(repo_path) / "requirements.txt"
    requirements_path.parent.mkdir(parents=True, exist_ok=True)

    existing: set[str] = set()
    if requirements_path.exists():
        existing = {
            line.strip()
            for line in requirements_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

    packages_to_install: list[str] = []
    for module in sorted(missing_modules):
        package = _map_module_to_package(module)
        if package not in existing:
            packages_to_install.append(package)

    if packages_to_install:
        with requirements_path.open("a", encoding="utf-8") as f:
            for package in packages_to_install:
                f.write(f"{package}\n")

    installed: list[str] = []
    for package in packages_to_install or [_map_module_to_package(m) for m in missing_modules]:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,
                capture_output=True,
                text=True,
            )
            installed.append(package)
        except subprocess.CalledProcessError:
            continue

    return bool(installed or packages_to_install), installed, packages_to_install


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, help="caminho para spec.yaml")
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

    auto_deps_installed: list[str] = []
    auto_deps_declared: list[str] = []

    data = run_planner_coder(router, repo_path, args.spec)
    patches = data["patches"]
    test_plan = data["test_plan"]
    state.log({"event": "planner_coder_done", "patch_count": len(patches)})

    apply_patches(repo_path, patches)

    tests = run_tester(router, patches, test_plan)
    test_patches = tests["patches"]
    apply_patches(repo_path, test_patches)
    state.log({"event": "tester_done", "test_patch_count": len(test_patches)})

    ok, test_output = run_pytests(repo_path)
    if not ok:
        missing = _extract_missing_modules(test_output)
        ensured, installed, declared = _ensure_dependencies(repo_path, missing)
        if ensured:
            auto_deps_installed.extend(installed)
            auto_deps_declared.extend(declared)
            state.log(
                {
                    "event": "auto_dependency_install",
                    "missing_modules": sorted(missing),
                    "packages_installed": installed,
                    "packages_declared": declared,
                }
            )
            ok, test_output = run_pytests(repo_path)
    state.log({"event": "pytest_result", "ok": ok, "output": test_output[:6000]})
    if not ok:
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
                "log_path": str(qa_result.log_path.relative_to(repo_path)),
            }
        )

    commit_push(repo_path, f"[autobot] apply patches and tests - {run_id}", branch)

    review_md = run_reviewer(router, repo_path, context="MVP 4 nA3s")
    write_review(repo_path, review_md)
    commit_push(repo_path, f"[autobot] add REVIEW.md - {run_id}", branch)
    state.log({"event": "reviewer_done"})

    metadata = {
        "run_id": run_id,
        "auto_dependencies_installed": auto_deps_installed,
        "auto_dependencies_declared": auto_deps_declared,
        "qa_report": str(qa_result.report_path.relative_to(repo_path)),
        "qa_overlay": str(qa_result.overlay_path.relative_to(repo_path)),
    }
    pr_body = run_pr_integrator(
        router,
        pr_title=f"Autobot PR {run_id}",
        default_body=review_md,
        metadata=metadata,
    )
    pr_number = open_pr(branch, f"Autobot PR {run_id}", pr_body)
    state.log({"event": "pr_opened", "pr_number": pr_number})
    print(f"PR aberto: #{pr_number}")


if __name__ == "__main__":
    main()
