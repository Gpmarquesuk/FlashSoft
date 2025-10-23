import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.interview_assistant.orchestration.pipeline import run_cli


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")


class DummyGenerator:
    def __init__(self, *args, **kwargs):
        pass

    def generate(self, question, resume_chunks, jd_chunks, transcript):
        return {
            "final_answer": f"Resposta para {question}",
            "talking_points": ["Fale sobre Whisper", "RAG em baixa latencia"],
            "sources": ["curriculo", "job description"],
        }


def _build_docx(path: Path):
    from docx import Document

    document = Document()
    document.add_paragraph("Experiencia com entrevistas ao vivo.")
    document.save(path)


def _build_pdf(path: Path):
    path.write_text("Fake PDF content", encoding="utf-8")


@patch("src.interview_assistant.orchestration.pipeline.InterviewResponseGenerator", lambda config: DummyGenerator())
def test_cli_pipeline(tmp_path: Path):
    resume = tmp_path / "resume.pdf"
    jd = tmp_path / "jd.docx"
    _build_pdf(resume)
    _build_docx(jd)

    output_dir = tmp_path / "artifacts"
    logs_dir = tmp_path / "logs"

    result = run_cli(
        resume=resume,
        jd=jd,
        question="Como voce lidera times?",
        output_dir=output_dir,
        logs_dir=logs_dir,
        model="openai/gpt-4o-mini",
        enable_audio=False,
        enable_overlay_gui=False,
    )

    artifact = json.loads((output_dir / "last_answer.json").read_text(encoding="utf-8"))
    assert "Resposta para" in artifact["final_answer"]
    assert (output_dir / "overlay.html").exists()
    assert (logs_dir / "metrics.jsonl").exists()
    assert result["final_answer"].startswith("Resposta")
