import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import structlog

from app.agents.embedding import EmbeddingAgent
from app.agents.extraction import ExtractionAgent
from app.agents.indexing import IndexingAgent
from app.services.document_service import DocumentService
from app.services.storage_service import StorageService


class PipelineOrchestrator:
    def __init__(
        self,
        document_service: DocumentService,
        storage_service: StorageService,
        extraction_agent: ExtractionAgent,
        embedding_agent: EmbeddingAgent,
        indexing_agent: IndexingAgent,
        *,
        max_concurrent_jobs: int,
    ) -> None:
        self.document_service = document_service
        self.storage_service = storage_service
        self.extraction_agent = extraction_agent
        self.embedding_agent = embedding_agent
        self.indexing_agent = indexing_agent
        self.logger = structlog.get_logger("pipeline")
        self.semaphore = asyncio.Semaphore(max_concurrent_jobs)
        self.active_tasks: dict[str, asyncio.Task[None]] = {}

    async def submit(self, document_id: str) -> None:
        task = asyncio.create_task(self._run(document_id))
        self.active_tasks[document_id] = task

    async def recover(self, stale_ids: list[str]) -> None:
        for document_id in stale_ids:
            await self.submit(document_id)

    async def _run(self, document_id: str) -> None:
        async with self.semaphore:
            record = self.document_service.store.documents.get(document_id)
            if record is None:
                return

            blob_bytes = await self.storage_service.get_blob_bytes(record["blob_url"])
            if blob_bytes is None:
                await self.document_service.mark_failed(document_id, "extraction", "Source file is unavailable.")
                return

            try:
                await self._log_and_update(document_id, "extraction", "processing", "in_progress")
                chunks, page_count = await self.extraction_agent.extract(document_id, record["user_id"], blob_bytes)

                await self._log_and_update(document_id, "embedding", "processing", "in_progress", page_count=page_count)
                embedded_chunks = await self.embedding_agent.embed(chunks)

                await self._log_and_update(document_id, "indexing", "processing", "in_progress", page_count=page_count)
                chunk_count = await self.indexing_agent.index(embedded_chunks)
                await self.document_service.mark_completed(document_id, chunk_count=chunk_count, page_count=page_count)
                self.logger.info("indexing_completed", document_id=document_id, chunk_count=chunk_count)
            except Exception as exc:  # pragma: no cover - defensive boundary
                await self.document_service.mark_failed(document_id, "indexing", str(exc))
                self.logger.error("pipeline_failed", document_id=document_id, error=str(exc))
            finally:
                self.active_tasks.pop(document_id, None)

    async def _log_and_update(
        self,
        document_id: str,
        stage: str,
        status: str,
        stage_state: str,
        *,
        page_count: int | None = None,
    ) -> None:
        self.logger.info(f"{stage}_started", document_id=document_id, stage=stage)
        await self.document_service.update_stage(
            document_id,
            status=status,
            stage=stage,
            stage_state=stage_state,
            page_count=page_count,
        )

