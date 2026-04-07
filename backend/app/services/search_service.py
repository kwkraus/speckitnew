import math
import re
from collections import Counter
from typing import Any

from app.config import Settings
from app.models.chunk import ContentChunk
from app.services.runtime_store import RuntimeStore


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9']+")


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


class SearchService:
    def __init__(self, settings: Settings, store: RuntimeStore) -> None:
        self.settings = settings
        self.store = store

    async def ensure_index_exists(self) -> None:
        self.store.search_index_ready = True

    async def add_documents(self, chunks: list[ContentChunk]) -> None:
        for chunk in chunks:
            self.store.chunks[chunk.id] = chunk.model_dump()

    async def delete_by_document_id(self, document_id: str) -> None:
        to_remove = [chunk_id for chunk_id, chunk in self.store.chunks.items() if chunk["document_id"] == document_id]
        for chunk_id in to_remove:
            self.store.chunks.pop(chunk_id, None)

    async def hybrid_search(
        self,
        query: str,
        user_id: str,
        query_vector: list[float] | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        query_terms = Counter(_tokenize(query))
        results: list[tuple[float, dict[str, Any]]] = []

        for chunk in self.store.chunks.values():
            if chunk["user_id"] != user_id:
                continue
            content_terms = Counter(_tokenize(chunk["content"]))
            lexical_score = sum(min(query_terms[token], content_terms[token]) for token in query_terms)
            vector_score = self._cosine_similarity(query_vector or [], chunk.get("embedding", []))
            score = lexical_score + vector_score
            if score > 0:
                results.append((score, chunk))

        results.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                **chunk,
                "@search.score": round(score, 4),
            }
            for score, chunk in results[:top_k]
        ]

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        numerator = sum(a * b for a, b in zip(left, right, strict=False))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

