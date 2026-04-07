import pytest

from app.auth.dependencies import CurrentUser
from app.config import Settings
from app.models.chunk import ContentChunk
from app.services.chat_service import ChatService
from app.services.runtime_store import RuntimeStore
from app.services.search_service import SearchService


@pytest.mark.asyncio
async def test_chat_service_builds_grounded_answer():
    store = RuntimeStore()
    store.documents["doc-1"] = {
        "id": "doc-1",
        "user_id": "user-1",
        "filename": "quarterly-report.pdf",
        "status": "completed",
        "file_size": 100,
        "page_count": 1,
        "chunk_count": 1,
        "error_message": None,
        "blob_url": "memory://pdf-uploads/doc-1",
        "progress": {"extraction": "completed", "embedding": "completed", "indexing": "completed"},
        "created_at": __import__("datetime").datetime.now(__import__("datetime").UTC),
        "updated_at": __import__("datetime").datetime.now(__import__("datetime").UTC),
        "content_hash": "hash",
    }
    search = SearchService(Settings(), store)
    chat = ChatService(store, search)
    user = CurrentUser(user_id="user-1", display_name="Ada")
    await chat.create_conversation(user, "Revenue")
    conversation_id = next(iter(store.conversations))

    await search.add_documents(
        [
            ContentChunk(
                id="doc-1_0",
                document_id="doc-1",
                user_id="user-1",
                chunk_index=0,
                content="Q4 revenue was 12.3 million dollars and growth reached 15 percent.",
                embedding=[0.2] * 1536,
            )
        ]
    )

    response = await chat.send_message(user, conversation_id, "What was Q4 revenue?")
    assert response is not None
    assert response.assistant_message.citations
    assert "12.3 million" in response.assistant_message.content

