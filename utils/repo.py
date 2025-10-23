from __future__ import annotations

import shutil
from pathlib import Path


def normalise_interview_package(repo_path: str | Path) -> None:
    """
    Ensure legacy package layouts are migrated to `src/interview_assistant`.
    Idempotent; safe to run multiple times.
    """
    repo = Path(repo_path)
    legacy_pkg = repo / "src" / "interview"
    target_pkg = repo / "src" / "interview_assistant"
    if not legacy_pkg.exists():
        return

    if target_pkg.exists():
        shutil.rmtree(target_pkg)
    shutil.move(str(legacy_pkg), str(target_pkg))

    replacements = {
        "from interview.": "from interview_assistant.",
        "from interview import": "from interview_assistant import",
        "from src.interview": "from src.interview_assistant",
        "import interview.": "import interview_assistant.",
        "import interview ": "import interview_assistant ",
        "import interview\n": "import interview_assistant\n",
        "import src.interview": "import src.interview_assistant",
    }

    for py_file in repo.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        new_text = text
        for old, new in replacements.items():
            new_text = new_text.replace(old, new)
        if new_text != text:
            py_file.write_text(new_text, encoding="utf-8")

    init_path = target_pkg / "__init__.py"
    init_path.write_text(
        "from .assistant import *\nInterviewAssistant = Assistant\n",
        encoding="utf-8",
    )
