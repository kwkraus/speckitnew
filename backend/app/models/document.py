from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


StageState = Literal["pending", "in_progress", "completed", "failed"]
DocumentState = Literal["pending", "processing", "completed", "failed", "deleting"]


class StageProgress(BaseModel):
    extraction: StageState = "pending"
    embedding: StageState = "pending"
    indexing: StageState = "pending"


class DocumentCreate(BaseModel):
    filename: str
    file_size: int


class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: DocumentState
    file_size: int
    page_count: int | None = None
    chunk_count: int | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DocumentStatusResponse(BaseModel):
    id: str
    status: DocumentState
    stage: str = "queued"
    progress: StageProgress = Field(default_factory=StageProgress)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error_message: str | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int

