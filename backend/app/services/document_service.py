import hashlib
from datetime import UTC, datetime
from uuid import uuid4

from app.auth.dependencies import CurrentUser
from app.models.document import DocumentListResponse, DocumentResponse, DocumentStatusResponse, StageProgress
from app.services.runtime_store import RuntimeStore
from app.services.search_service import SearchService
from app.services.storage_service import StorageService


class DocumentService:
    def __init__(
        self,
        store: RuntimeStore,
        storage_service: StorageService,
        search_service: SearchService,
    ) -> None:
        self.store = store
        self.storage_service = storage_service
        self.search_service = search_service

    async def ensure_storage(self) -> None:
        self.store.cosmos_ready = True

    async def create_document(
        self,
        user: CurrentUser,
        filename: str,
        file_size: int,
        data: bytes,
    ) -> tuple[dict, dict | None]:
        content_hash = hashlib.sha256(data).hexdigest()
        existing = self._find_duplicate(user.user_id, content_hash)
        if existing is not None:
            return {}, existing

        document_id = str(uuid4())
        blob_url = await self.storage_service.upload_blob(user.user_id, document_id, filename, data)
        now = datetime.now(UTC)
        record = {
            "id": document_id,
            "user_id": user.user_id,
            "filename": filename,
            "content_hash": content_hash,
            "blob_url": blob_url,
            "status": "pending",
            "file_size": file_size,
            "page_count": None,
            "chunk_count": None,
            "error_message": None,
            "progress": {
                "extraction": "pending",
                "embedding": "pending",
                "indexing": "pending",
            },
            "created_at": now,
            "updated_at": now,
        }
        self.store.documents[document_id] = record
        return record, None

    async def list_documents(
        self,
        user_id: str,
        page: int,
        page_size: int,
        status_filter: str | None = None,
    ) -> DocumentListResponse:
        documents = [
            record
            for record in self.store.documents.values()
            if record["user_id"] == user_id and (status_filter is None or record["status"] == status_filter)
        ]
        documents.sort(key=lambda item: item["created_at"], reverse=True)
        start = max(page - 1, 0) * page_size
        end = start + page_size
        items = [DocumentResponse(**doc) for doc in documents[start:end]]
        return DocumentListResponse(documents=items, total=len(documents), page=page, page_size=page_size)

    async def get_document(self, user_id: str, document_id: str) -> DocumentResponse | None:
        record = self.store.documents.get(document_id)
        if record is None or record["user_id"] != user_id:
            return None
        return DocumentResponse(**record)

    async def get_status(self, user_id: str, document_id: str) -> DocumentStatusResponse | None:
        record = self.store.documents.get(document_id)
        if record is None or record["user_id"] != user_id:
            return None

        current_stage = "queued"
        for stage_name, stage_state in record["progress"].items():
            if stage_state == "in_progress":
                current_stage = stage_name
                break
            if stage_state == "completed":
                current_stage = stage_name

        return DocumentStatusResponse(
            id=record["id"],
            status=record["status"],
            stage=current_stage,
            progress=StageProgress(**record["progress"]),
            updated_at=record["updated_at"],
            error_message=record["error_message"],
        )

    async def update_stage(
        self,
        document_id: str,
        *,
        status: str,
        stage: str,
        stage_state: str,
        page_count: int | None = None,
        chunk_count: int | None = None,
        error_message: str | None = None,
    ) -> None:
        record = self.store.documents[document_id]
        record["status"] = status
        record["progress"][stage] = stage_state
        record["updated_at"] = datetime.now(UTC)
        if page_count is not None:
            record["page_count"] = page_count
        if chunk_count is not None:
            record["chunk_count"] = chunk_count
        record["error_message"] = error_message

    async def mark_failed(self, document_id: str, stage: str, message: str) -> None:
        await self.update_stage(document_id, status="failed", stage=stage, stage_state="failed", error_message=message)

    async def mark_completed(self, document_id: str, chunk_count: int, page_count: int) -> None:
        record = self.store.documents[document_id]
        record["status"] = "completed"
        record["progress"] = {
            "extraction": "completed",
            "embedding": "completed",
            "indexing": "completed",
        }
        record["chunk_count"] = chunk_count
        record["page_count"] = page_count
        record["updated_at"] = datetime.now(UTC)

    async def delete_document(self, user_id: str, document_id: str) -> DocumentResponse | None:
        record = self.store.documents.get(document_id)
        if record is None or record["user_id"] != user_id:
            return None
        record["status"] = "deleting"
        await self.search_service.delete_by_document_id(document_id)
        await self.storage_service.delete_blob(record["blob_url"])
        removed = self.store.documents.pop(document_id)
        return DocumentResponse(**removed)

    async def replace_document(
        self,
        user: CurrentUser,
        document_id: str,
        filename: str,
        file_size: int,
        data: bytes,
    ) -> tuple[dict, dict | None]:
        await self.delete_document(user.user_id, document_id)
        return await self.create_document(user, filename, file_size, data)

    async def recover_stale_jobs(self) -> list[str]:
        stale_ids = [doc_id for doc_id, record in self.store.documents.items() if record["status"] == "processing"]
        for doc_id in stale_ids:
            record = self.store.documents[doc_id]
            record["status"] = "pending"
        return stale_ids

    def has_completed_documents(self, user_id: str) -> bool:
        return any(
            record["user_id"] == user_id and record["status"] == "completed"
            for record in self.store.documents.values()
        )

    def _find_duplicate(self, user_id: str, content_hash: str) -> dict | None:
        for record in self.store.documents.values():
            if record["user_id"] == user_id and record["content_hash"] == content_hash:
                return {
                    "id": record["id"],
                    "filename": record["filename"],
                    "created_at": record["created_at"].isoformat(),
                }
        return None

