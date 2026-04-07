from app.models.chunk import ContentChunk
from app.services.search_service import SearchService


class IndexingAgent:
    def __init__(self, search_service: SearchService) -> None:
        self.search_service = search_service

    async def index(self, chunks: list[ContentChunk]) -> int:
        await self.search_service.add_documents(chunks)
        return len(chunks)

    async def delete_by_document_id(self, document_id: str) -> None:
        await self.search_service.delete_by_document_id(document_id)

