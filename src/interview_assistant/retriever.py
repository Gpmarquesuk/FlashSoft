import re


class Retriever:
    def __init__(self):
        self.documents = []

    def add_document(self, doc_id, text):
        self.documents.append({'id': doc_id, 'text': text})

    def _chunk_text(self, text, chunk_size=100):
        # Simple word-based chunking
        words = re.findall(r'\w+', text.lower())
        chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
        return chunks

    def _score_chunk(self, chunk, query):
        query_words = set(re.findall(r'\w+', query.lower()))
        chunk_words = set(re.findall(r'\w+', chunk.lower()))
        if not query_words:
            return 0.0
        intersection = len(query_words & chunk_words)
        return intersection / len(query_words)

    def retrieve(self, query, top_k=5):
        all_chunks = []
        for doc in self.documents:
            chunks = self._chunk_text(doc['text'])
            for chunk in chunks:
                score = self._score_chunk(chunk, query)
                if score > 0:
                    all_chunks.append({
                        'text': chunk,
                        'doc_id': doc['id'],
                        'score': score
                    })
        all_chunks.sort(key=lambda x: x['score'], reverse=True)
        return all_chunks[:top_k]