from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

from utils.repo import normalise_interview_package


MODULE_PACKAGE_OVERRIDES = {
    "yaml": "PyYAML",
    "pil": "Pillow",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "bs4": "beautifulsoup4",
}


def _sanitize_pytest_ini(repo_path: str) -> None:
    path = Path(repo_path) / "pytest.ini"
    if not path.exists():
        return
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines or lines[0].lower() != "[pytest]":
        path.write_text("[pytest]\n", encoding="utf-8")


def run_pytests(repo_path: str, extra_env: dict | None = None, timeout: int = 300) -> Tuple[bool, str]:
    env = os.environ.copy()
    env.setdefault("USE_FREE_MODELS", "1")
    if extra_env:
        env.update(extra_env)
    try:
        out = subprocess.run(
            ["pytest", "-q"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        ok = out.returncode == 0
        return ok, out.stdout + "\n" + out.stderr
    except Exception as exc:
        return False, str(exc)


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
    return MODULE_PACKAGE_OVERRIDES.get(module.lower(), module)


def _ensure_dependencies(repo_path: str, missing_modules: set[str]) -> Tuple[bool, List[str], List[str]]:
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

    packages_to_install: List[str] = []
    for module in sorted(missing_modules):
        package = _map_module_to_package(module)
        if package not in existing:
            packages_to_install.append(package)

    if packages_to_install:
        with requirements_path.open("a", encoding="utf-8") as fh:
            for package in packages_to_install:
                fh.write(f"{package}\n")

    installed: List[str] = []
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


def run_integrator(repo_path: str) -> dict:
    """
    Executa pytest e tenta instalar dependencias faltantes. Nao ha fallback silencioso.
    """
    result = {
        "pytest_ok": False,
        "pytest_output": "",
        "missing_modules": [],
        "dependencies_installed": [],
        "dependencies_declared": [],
        "baseline_applied": False,
    }

    _sanitize_pytest_ini(repo_path)
    ok, output = run_pytests(repo_path)
    result["pytest_ok"] = ok
    result["pytest_output"] = output[:6000]

    if ok:
        return result

    missing = _extract_missing_modules(output)
    result["missing_modules"] = sorted(missing)
    ensured, installed, declared = _ensure_dependencies(repo_path, missing)
    if ensured:
        result["dependencies_installed"] = installed
        result["dependencies_declared"] = declared
        normalise_interview_package(repo_path)
        ok, output = run_pytests(repo_path)
        result["pytest_ok"] = ok
        result["pytest_output"] = output[:6000]

    return result
