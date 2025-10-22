from pathlib import Path

from src.interview_assistant.assistant import run_cli


def test_cli_creates_artifacts(sample_paths, tmp_path: Path):
    resume, jd = sample_paths
    output_dir = tmp_path / "artifacts"
    logs_dir = tmp_path / "logs"
    run_cli(str(resume), str(jd), "Why should we hire you?", str(output_dir), str(logs_dir))
    assert (output_dir / "last_answer.json").exists()
    assert list((logs_dir / "agent_chat").glob("*.md"))
