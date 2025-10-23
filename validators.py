import subprocess
from pathlib import Path
from typing import Iterable, List, Tuple


def check_syntax(paths: Iterable[Path]) -> List[Tuple[Path, str]]:
    """
    Run `python -m py_compile` for the provided python files.
    Returns list of (path, error_message) for files with syntax issues.
    """
    errors: List[Tuple[Path, str]] = []
    for path in paths:
        if not path.exists():
            continue
        if path.suffix != ".py":
            continue
        try:
            subprocess.run(
                ["python", "-m", "py_compile", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            msg = exc.stderr.strip() or exc.stdout.strip() or exc.__class__.__name__
            errors.append((path, msg))
    return errors
