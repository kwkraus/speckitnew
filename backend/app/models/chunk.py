from pydantic import BaseModel, Field


class ContentChunk(BaseModel):
    id: str
    document_id: str
    user_id: str
    document_name: str | None = None
    chunk_index: int
    content: str
    section_title: str | None = None
    page_number: int = 1
    embedding: list[float] = Field(default_factory=list)
    token_count: int = 0

