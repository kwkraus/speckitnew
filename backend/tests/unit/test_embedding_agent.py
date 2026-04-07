import pytest

from app.agents.embedding import EmbeddingAgent
from app.models.chunk import ContentChunk


@pytest.mark.asyncio
async def test_embedding_returns_1536_dimension_vectors():
    agent = EmbeddingAgent()
    chunks = [
        ContentChunk(
            id="doc_0",
            document_id="doc",
            user_id="user",
            chunk_index=0,
            content="The quarter closed with 12.3M in revenue.",
        )
    ]

    enriched = await agent.embed(chunks)
    assert len(enriched[0].embedding) == 1536

