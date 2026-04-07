import pytest

from app.agents.extraction import ExtractionAgent
from app.config import Settings


@pytest.mark.asyncio
async def test_extract_returns_chunk_ready_payloads():
    agent = ExtractionAgent(Settings())
    chunks, page_count = await agent.extract(
        "doc-1",
        "user-1",
        b"%PDF-1.4\nOverview\n\nA short paragraph about revenue and growth.\n%%EOF",
    )

    assert page_count == 1
    assert chunks[0].document_id == "doc-1"
    assert chunks[0].page_number == 1


@pytest.mark.asyncio
async def test_extract_uses_ocr_fallback_for_scanned_pdfs():
    agent = ExtractionAgent(Settings())
    chunks, _ = await agent.extract("doc-2", "user-1", b"")

    assert "OCR fallback" in chunks[0].content


@pytest.mark.asyncio
async def test_extract_rejects_encrypted_pdf(monkeypatch):
    class EncryptedReader:
        is_encrypted = True

    monkeypatch.setattr("app.agents.extraction.PdfReader", lambda _: EncryptedReader())
    agent = ExtractionAgent(Settings())

    chunks, _ = await agent.extract("doc-3", "user-1", b"%PDF-1.4")
    assert chunks

