import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_paths(tmp_path: Path) -> tuple[Path, Path]:
    resume = tmp_path / "resume.json"
    resume.write_text(
        json.dumps(
            {
                "name": "Alex Candidate",
                "summary": "Experienced engineer",
                "achievements": [
                    "Built realtime assistants",
                    "Integrated resume and job description guidance",
                ],
            }
        ),
        encoding="utf-8",
    )
    jd = tmp_path / "jd.md"
    jd.write_text("We need realtime interview guidance.", encoding="utf-8")
    return resume, jd
