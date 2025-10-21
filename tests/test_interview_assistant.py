import pytest
import json
import subprocess
from pathlib import Path
import uuid

@pytest.fixture
def sample_files(tmp_path):
    resume = tmp_path / "resume.json"
    resume.write_text('{"name": "John Doe"}')
    jd = tmp_path / "jd.md"
    jd.write_text('# Job Description')
    return {'resume': str(resume), 'jd': str(jd)}

@pytest.fixture
def artifacts_dir(tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    return artifacts

@pytest.fixture
def logs_dir(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    return logs

def test_retrieval_basic(sample_files):
    # Positive test
    result = subprocess.run(
        ['python', '-m', 'src.interview_assistant',
         '--resume', sample_files['resume'],
         '--jd', sample_files['jd'],
         '--question', 'What is your experience?'],
        capture_output=True
    )
    assert result.returncode == 0
    
    # Negative test - invalid file
    with pytest.raises(Exception):
        subprocess.run(
            ['python', '-m', 'src.interview_assistant',
             '--resume', 'invalid.json',
             '--jd', sample_files['jd'],
             '--question', 'test'],
            check=True
        )

def test_answer_shape(sample_files, artifacts_dir):
    subprocess.run(
        ['python', '-m', 'src.interview_assistant',
         '--resume', sample_files['resume'],
         '--jd', sample_files['jd'],
         '--question', 'What is your experience?',
         '--output-dir', str(artifacts_dir)],
        capture_output=True
    )
    
    with open(artifacts_dir / 'last_answer.json') as f:
        answer = json.load(f)
        
    assert 'final_answer' in answer
    assert 'talking_points' in answer
    assert 'sources' in answer
    assert len(answer['final_answer'].split()) <= 120

def test_overlay_fallback(sample_files, artifacts_dir):
    subprocess.run(
        ['python', '-m', 'src.interview_assistant',
         '--resume', sample_files['resume'],
         '--jd', sample_files['jd'],
         '--question', 'What is your experience?',
         '--output-dir', str(artifacts_dir)],
        capture_output=True
    )
    
    overlay = artifacts_dir / 'overlay.html'
    assert overlay.exists()
    
    content = overlay.read_text()
    assert '<html' in content
    assert 'John Doe' in content

def test_observability(sample_files, logs_dir):
    result = subprocess.run(
        ['python', '-m', 'src.interview_assistant',
         '--resume', sample_files['resume'],
         '--jd', sample_files['jd'],
         '--question', 'What is your experience?',
         '--logs-dir', str(logs_dir)],
        capture_output=True
    )
    
    log_files = list(logs_dir.glob('agent_chat/*.md'))
    assert len(log_files) == 1
    
    log_content = log_files[0].read_text()
    assert '# Chat Log' in log_content
    assert 'Question: What is your experience?' in log_content
    assert 'Final Answer:' in log_content
