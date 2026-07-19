from __future__ import annotations

import math
import re
from dataclasses import dataclass

from services.documents import Chunk


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float


class SemanticRetriever:
    """优先使用本地中文向量检索，加载失败时退回关键词检索。"""

    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.mode = "未构建"
        self._model = None
        self._index = None
        self._vectors = None

    def search(self, query: str, limit: int = 4) -> list[RetrievedChunk]:
        if not self.chunks:
            return []
        try:
            return self._semantic_search(query, limit)
        except Exception:  # noqa: BLE001
            self.mode = "关键词检索（向量模型暂不可用）"
            return self._keyword_search(query, limit)

    def _semantic_search(self, query: str, limit: int) -> list[RetrievedChunk]:
        import faiss
        import numpy as np
        from sentence_transformers import SentenceTransformer

        if self._model is None:
            self._model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
            texts = [f"{chunk.title}\n{chunk.content}" for chunk in self.chunks]
            self._vectors = self._model.encode(texts, normalize_embeddings=True)
            self._index = faiss.IndexFlatIP(self._vectors.shape[1])
            self._index.add(np.asarray(self._vectors, dtype="float32"))
        query_vector = self._model.encode([query], normalize_embeddings=True)
        scores, indexes = self._index.search(
            np.asarray(query_vector, dtype="float32"), min(limit, len(self.chunks))
        )
        self.mode = "本地中文语义检索"
        return [
            RetrievedChunk(self.chunks[index], float(score))
            for score, index in zip(scores[0], indexes[0])
            if index >= 0
        ]

    def _keyword_search(self, query: str, limit: int) -> list[RetrievedChunk]:
        query_terms = set(re.findall(r"[\u4e00-\u9fff]{1,}|[a-zA-Z0-9_-]+", query.lower()))
        scored: list[RetrievedChunk] = []
        for chunk in self.chunks:
            text = f"{chunk.title} {chunk.content}".lower()
            matched = sum(1 for term in query_terms if term in text)
            score = matched / math.sqrt(max(len(text), 1))
            scored.append(RetrievedChunk(chunk, score))
        return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]
