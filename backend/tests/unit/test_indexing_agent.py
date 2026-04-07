import pytest

from app.agents.indexing import IndexingAgent
from app.config import Settings
from app.models.chunk import ContentChunk
from app.services.runtime_store import RuntimeStore
from app.services.search_service import SearchService


@pytest.mark.asyncio
async def test_indexing_agent_upserts_and_deletes_documents():
    store = RuntimeStore()
    service = SearchService(Settings(), store)
    agent = IndexingAgent(service)
    chunk = ContentChunk(
        id="doc_0",
        document_id="doc",
        user_id="user",
        chunk_index=0,
        content="Operational savings improved by 8 percent.",
        embedding=[0.1] * 1536,
    )

    count = await agent.index([chunk])
    assert count == 1
    assert "doc_0" in store.chunks

    await agent.delete_by_document_id("doc")
    assert "doc_0" not in store.chunks

