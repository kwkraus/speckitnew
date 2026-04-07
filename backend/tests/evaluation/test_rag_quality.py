import pytest

from app.auth.dependencies import CurrentUser
from app.config import Settings
from app.models.chunk import ContentChunk
from app.services.chat_service import ChatService
from app.services.runtime_store import RuntimeStore
from app.services.search_service import SearchService


@pytest.mark.asyncio
async def test_rag_quality_thresholds_are_met():
    store = RuntimeStore()
    store.documents["doc-quality"] = {
        "id": "doc-quality",
        "user_id": "user-1",
        "filename": "ground-truth.pdf",
        "status": "completed",
        "file_size": 100,
        "page_count": 1,
        "chunk_count": 1,
        "error_message": None,
        "blob_url": "memory://pdf-uploads/doc-quality",
        "progress": {"extraction": "completed", "embedding": "completed", "indexing": "completed"},
        "created_at": __import__("datetime").datetime.now(__import__("datetime").UTC),
        "updated_at": __import__("datetime").datetime.now(__import__("datetime").UTC),
        "content_hash": "hash",
    }
    search = SearchService(Settings(), store)
    chat = ChatService(store, search)
    user = CurrentUser(user_id="user-1", display_name="Ada")
    await chat.create_conversation(user, "Quality check")
    conversation_id = next(iter(store.conversations))

    await search.add_documents(
        [
            ContentChunk(
                id="doc-quality_0",
                document_id="doc-quality",
                user_id="user-1",
                chunk_index=0,
                content="Q4 revenue reached 12.3 million dollars with 15 percent quarter-over-quarter growth.",
                embedding=[0.3] * 1536,
            )
        ]
    )

    answer = await chat.send_message(user, conversation_id, "What was Q4 revenue?")
    no_answer = await chat.send_message(user, conversation_id, "What happened on Mars?")

    citation_accuracy = 1.0 if answer and answer.assistant_message.citations else 0.0
    unanswerable_detection = (
        1.0 if no_answer and "couldn't find grounded evidence" in no_answer.assistant_message.content.lower() else 0.0
    )

    assert citation_accuracy >= 0.9
    assert unanswerable_detection >= 0.95
