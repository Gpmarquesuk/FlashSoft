import pytest
from src.interview_assistant.retriever import Retriever

@pytest.fixture
def sample_document():
    return "This is a sample document containing relevant terms for testing retrieval functionality."

@pytest.fixture
def retriever(sample_document):
    return Retriever(sample_document)

@pytest.mark.parametrize("query, expected_in_top_chunk", [
    ("relevant terms", True),
    ("nonexistent term", False)
])
def test_retrieval_basic(retriever, query, expected_in_top_chunk):
    chunks = retriever.retrieve(query)
    assert len(chunks) > 0
    assert all(chunk['score'] > 0 for chunk in chunks)
    assert (query in chunks[0]['content']) == expected_in_top_chunk
