from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors


@dataclass
class RetrievedChunk:
    text: str
    score: float
    source: str


class VectorStore:
    def __init__(self, top_k: int = 5) -> None:
        self.top_k = top_k
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._index: Optional[NearestNeighbors] = None
        self._docs: List[str] = []
        self._metadata: List[str] = []
        self._fitted = False

    def build_index(self, corpus: Dict[str, Iterable[str]]) -> None:
        texts: List[str] = []
        meta: List[str] = []
        for source, lines in corpus.items():
            for line in lines:
                if line:
                    texts.append(line)
                    meta.append(source)
        if not texts:
            raise ValueError("Corpus vazio")
        vectors = self._vectorizer.fit_transform(texts)
        n_neighbors = min(self.top_k, len(texts))
        self._index = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
        self._index.fit(vectors)
        self._docs = texts
        self._metadata = meta
        self._fitted = True

    def query(self, question: str) -> List[RetrievedChunk]:
        if not self._fitted or self._index is None:
            raise RuntimeError("Index ainda nao foi construido")
        query_vec = self._vectorizer.transform([question])
        distances, indices = self._index.kneighbors(query_vec, return_distance=True)
        results: List[RetrievedChunk] = []
        for dist, idx in zip(distances[0], indices[0]):
            score = 1 - float(dist)
            results.append(
                RetrievedChunk(
                    text=self._docs[idx],
                    score=score,
                    source=self._metadata[idx],
                )
            )
        return results
