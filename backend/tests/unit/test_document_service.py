import pytest

from app.auth.dependencies import CurrentUser
from app.config import Settings
from app.services.document_service import DocumentService
from app.services.runtime_store import RuntimeStore
from app.services.search_service import SearchService
from app.services.storage_service import StorageService


@pytest.mark.asyncio
async def test_document_service_creates_duplicates_and_recovers_processing_jobs():
    store = RuntimeStore()
    storage = StorageService(Settings(), store)
    search = SearchService(Settings(), store)
    service = DocumentService(store, storage, search)
    user = CurrentUser(user_id="user-1", display_name="Ada")

    created, duplicate = await service.create_document(user, "report.pdf", 128, b"abc")
    assert duplicate is None
    assert created["status"] == "pending"

    _, duplicate = await service.create_document(user, "report.pdf", 128, b"abc")
    assert duplicate is not None

    await service.update_stage(created["id"], status="processing", stage="extraction", stage_state="in_progress")
    stale = await service.recover_stale_jobs()
    assert created["id"] in stale

