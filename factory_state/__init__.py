from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Optional


DEFAULT_STATE = {
    "releases": {},
    "latest": None,
}


@dataclass
class ReleaseRecord:
    run_id: str
    branch: str
    package: str
    sha256: str
    tests: Iterable[str]
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    release_tag: Optional[str] = None
    release_asset: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "run_id": self.run_id,
            "branch": self.branch,
            "package": self.package,
            "sha256": self.sha256,
            "tests": list(self.tests),
            "created_at": self.created_at,
            "release_tag": self.release_tag,
            "release_asset": self.release_asset,
        }


class FactoryState:
    """
    Simple JSON-backed state manager that tracks approved releases.

    The state file lives at factory_state/state.json and aggregates metadata
    from individual releases stored under factory_state/releases/<run_id>.json.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root or ".").resolve()
        self.state_path = self.root / "factory_state" / "state.json"
        if self.state_path.exists():
            self.data = json.loads(self.state_path.read_text(encoding="utf-8"))
        else:
            self.data = json.loads(json.dumps(DEFAULT_STATE))

    def record_release(self, record: ReleaseRecord) -> None:
        releases_dir = self.root / "factory_state" / "releases"
        releases_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = releases_dir / f"{record.run_id}.json"
        manifest_path.write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        self.data.setdefault("releases", {})
        self.data["releases"][record.run_id] = record.to_dict()
        self.data["latest"] = record.run_id
        self.save()

    def save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
