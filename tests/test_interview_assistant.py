import pytest
from src.interview_assistant import InterviewAssistant
import os
import json
from pathlib import Path

# Test data
RESUME_PATH = "data/resume.json"
JD_PATH = "data/jd.md"
QUESTION = "What is your experience with Python?"


# Test retrieval_basic

def test_retrieval_basic():
    assistant = InterviewAssistant(RESUME_PATH, JD_PATH)
    assert assistant.resume_data is not None, "Resume data should be loaded"
    assert assistant.jd_data is not None, "Job description data should be loaded"


# Test answer_shape

def test_answer_shape():
    assistant = InterviewAssistant(RESUME_PATH, JD_PATH)
    answer = assistant.answer(QUESTION)
    assert "answer" in answer, "Final answer should be present"
    assert "talking_points" in answer, "Talking points should be present"
    assert "sources" in answer, "Sources should be present"
    assert len(answer["answer"]) <= 120, "Final answer should be within 120 words"


# Test overlay_fallback

def test_overlay_fallback():
    assistant = InterviewAssistant(RESUME_PATH, JD_PATH)
    answer = assistant.answer(QUESTION)
    # Test HTML overlay
    html_overlay = assistant.generate_html_overlay(answer)
    assert "<html>" in html_overlay, "HTML overlay should be generated"
    # Test JSON artifact
    json_artifact = assistant.generate_json_artifact(answer)
    assert json.dumps(json_artifact) == json.dumps(answer), "JSON artifact should match the answer"


# Test observability

def test_observability():
    assistant = InterviewAssistant(RESUME_PATH, JD_PATH)
    run_id = assistant.run_id
    answer = assistant.answer(QUESTION)
    # Verify log file is created
    log_dir = Path("logs/agent_chat")
    log_file = log_dir / f"{run_id}.md"
    assert log_file.exists(), "Log file should be created"
    # Verify log content
    with open(log_file, "r") as f:
        log_content = f.read()
        assert QUESTION in log_content, "Question should be in log"
        assert answer["answer"] in log_content, "Answer should be in log"


# Test CLI command

def test_cli_command():
    import subprocess
    command = ["python", "-m", "src.interview_assistant", "--resume", RESUME_PATH, "--jd", JD_PATH, "--question", QUESTION]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, "CLI command should run successfully"
    # Verify output files
    assert os.path.exists("output/answer.html"), "HTML output file should be created"
    assert os.path.exists("output/answer.json"), "JSON output file should be created"
