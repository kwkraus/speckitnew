from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class CitationSchema(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    section_title: str | None = None
    snippet: str
    relevance: float


class MessageSchema(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    citations: list[CitationSchema] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationSummary(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageSchema] = Field(default_factory=list)


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummary]
    total: int
    page: int
    page_size: int


class MessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    user_message: MessageSchema
    assistant_message: MessageSchema

