import hashlib

from app.models.chunk import ContentChunk


class EmbeddingAgent:
    async def embed(self, chunks: list[ContentChunk]) -> list[ContentChunk]:
        enriched: list[ContentChunk] = []
        for chunk in chunks:
            vector = self._vector_from_text(chunk.content)
            enriched.append(chunk.model_copy(update={"embedding": vector}))
        return enriched

    @staticmethod
    def _vector_from_text(text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector: list[float] = []
        while len(vector) < 1536:
            for byte in digest:
                vector.append(round(byte / 255, 6))
                if len(vector) == 1536:
                    break
        return vector

