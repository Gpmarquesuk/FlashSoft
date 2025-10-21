import pytest
from unittest.mock import Mock
from src.interview_assistant.generator import Generator

@pytest.fixture
def mock_llm():
    llm = Mock()
    llm.generate.return_value = "# Final Answer\nThis is the final answer.\n# Talking Points\nThese are talking points.\n# Sources\nThese are sources."
    return llm

@pytest.fixture
def generator(mock_llm):
    return Generator(mock_llm)

def test_answer_shape(generator):
    output = generator.generate_answer("sample input")
    assert "# Final Answer" in output
    assert "# Talking Points" in output
    assert "# Sources" in output
    assert len(output.split()) <= 120
    # Assuming log file creation is handled within the generator
    # Check log file creation logic here if applicable
