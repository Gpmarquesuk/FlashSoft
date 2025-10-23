from src.interview_assistant.retrieval.vector_store import VectorStore


def test_vector_store_recall():
    store = VectorStore(top_k=3)
    corpus = {
        "resume": ["Experiencia em Whisper e PyAudio", "Projetos de RAG com FAISS"],
        "job": ["Buscamos Experiencia com transcricao em tempo real", "Uso de embeddings e vetores"],
    }
    store.build_index(corpus)
    results = store.query("transcricao em tempo real usando Whisper")
    assert results
    texts = " ".join(chunk.text for chunk in results)
    assert "Whisper" in texts or "transcricao" in texts
