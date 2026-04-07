from datetime import UTC, datetime
import re
from uuid import uuid4

from app.auth.dependencies import CurrentUser
from app.models.conversation import (
    CitationSchema,
    ConversationResponse,
    ConversationSummary,
    MessageResponse,
    MessageSchema,
)
from app.models.chunk import ContentChunk
from app.services.runtime_store import RuntimeStore
from app.services.search_service import SearchService


class ChatService:
    def __init__(self, store: RuntimeStore, search_service: SearchService) -> None:
        self.store = store
        self.search_service = search_service

    async def create_conversation(self, user: CurrentUser, title: str | None = None) -> ConversationResponse:
        now = datetime.now(UTC)
        conversation_id = str(uuid4())
        conversation = {
            "id": conversation_id,
            "user_id": user.user_id,
            "title": title or "New conversation",
            "created_at": now,
            "updated_at": now,
            "messages": [],
        }
        self.store.conversations[conversation_id] = conversation
        return ConversationResponse(**conversation)

    async def list_conversations(self, user: CurrentUser, page: int, page_size: int) -> list[ConversationSummary]:
        conversations = [
            conversation
            for conversation in self.store.conversations.values()
            if conversation["user_id"] == user.user_id
        ]
        conversations.sort(key=lambda item: item["updated_at"], reverse=True)
        start = max(page - 1, 0) * page_size
        end = start + page_size
        return [
            ConversationSummary(
                id=item["id"],
                title=item["title"],
                message_count=len(item["messages"]),
                created_at=item["created_at"],
                updated_at=item["updated_at"],
            )
            for item in conversations[start:end]
        ]

    async def get_conversation(self, user: CurrentUser, conversation_id: str) -> ConversationResponse | None:
        conversation = self.store.conversations.get(conversation_id)
        if conversation is None or conversation["user_id"] != user.user_id:
            return None
        return ConversationResponse(**conversation)

    async def delete_conversation(self, user: CurrentUser, conversation_id: str) -> bool:
        conversation = self.store.conversations.get(conversation_id)
        if conversation is None or conversation["user_id"] != user.user_id:
            return False
        self.store.conversations.pop(conversation_id, None)
        return True

    async def send_message(
        self,
        user: CurrentUser,
        conversation_id: str,
        content: str,
    ) -> MessageResponse | None:
        conversation = self.store.conversations.get(conversation_id)
        if conversation is None or conversation["user_id"] != user.user_id:
            return None

        query_embedding = self._embed_text(content)
        results = await self.search_service.hybrid_search(content, user.user_id, query_embedding, top_k=5)
        grounded_match = self._has_grounded_match(content, results)

        citations = [
            CitationSchema(
                chunk_id=result["id"],
                document_id=result["document_id"],
                document_name=self._document_name(result["document_id"]),
                page_number=result.get("page_number", 1),
                section_title=result.get("section_title"),
                snippet=result["content"][:200],
                relevance=min(0.99, max(0.2, float(result.get("@search.score", 0.5)) / 4)),
            )
            for result in results
        ] if grounded_match else []

        assistant_message = MessageSchema(
            id=str(uuid4()),
            role="assistant",
            content=self._build_answer(content, results if grounded_match else []),
            citations=citations,
        )
        user_message = MessageSchema(id=str(uuid4()), role="user", content=content)

        if conversation["title"] == "New conversation":
            conversation["title"] = content[:100]

        conversation["messages"].extend([user_message.model_dump(), assistant_message.model_dump()])
        conversation["updated_at"] = datetime.now(UTC)
        return MessageResponse(user_message=user_message, assistant_message=assistant_message)

    @staticmethod
    def _embed_text(text: str) -> list[float]:
        seed = sum(ord(char) for char in text)
        return [((seed + index * 13) % 101) / 100 for index in range(1536)]

    def _build_answer(self, question: str, results: list[dict]) -> str:
        if not results:
            return (
                "I couldn't find grounded evidence for that question in your indexed documents. "
                "Try uploading a relevant PDF or asking a narrower question."
            )

        bullet_points = []
        for index, result in enumerate(results[:3], start=1):
            summary = str(result["content"]).replace("\n", " ").strip()[:180]
            bullet_points.append(f"- {summary} [{index}]")

        return (
            f"Here is the most relevant evidence I found for **{question}**:\n\n"
            + "\n".join(bullet_points)
            + "\n\nEach citation links back to the source page in your document library."
        )

    def _document_name(self, document_id: str) -> str:
        document = self.store.documents.get(document_id)
        return str(document["filename"]) if document else "Unknown document"

    @staticmethod
    def _has_grounded_match(question: str, results: list[dict]) -> bool:
        stopwords = {
            "a",
            "an",
            "and",
            "are",
            "did",
            "do",
            "for",
            "happened",
            "how",
            "in",
            "is",
            "on",
            "the",
            "to",
            "was",
            "what",
            "when",
            "where",
            "who",
            "with",
        }
        query_terms = {
            token
            for token in re.findall(r"[a-z0-9']+", question.lower())
            if token not in stopwords and len(token) > 2
        }
        if not query_terms:
            return bool(results)

        for result in results:
            content_terms = set(re.findall(r"[a-z0-9']+", str(result.get("content", "")).lower()))
            if query_terms & content_terms:
                return True
        return False

    @staticmethod
    def seed_chunks(user_id: str, document_id: str, chunks: list[ContentChunk], store: RuntimeStore) -> None:
        for chunk in chunks:
            payload = chunk.model_dump()
            payload["user_id"] = user_id
            payload["document_id"] = document_id
            store.chunks[payload["id"]] = payload
