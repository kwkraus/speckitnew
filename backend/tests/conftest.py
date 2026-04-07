import time
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        test_client.app.state.store.documents.clear()
        test_client.app.state.store.conversations.clear()
        test_client.app.state.store.chunks.clear()
        test_client.app.state.store.blobs.clear()
        yield test_client
        test_client.app.state.store.documents.clear()
        test_client.app.state.store.conversations.clear()
        test_client.app.state.store.chunks.clear()
        test_client.app.state.store.blobs.clear()


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    return {"x-user-id": "user-123", "x-user-name": "Ada Lovelace"}


@pytest.fixture()
def sample_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\nRevenue Summary\n\nQ4 revenue was 12.3 million dollars.\n"
        b"The quarter grew by 15 percent over Q3.\n%%EOF"
    )


@pytest.fixture()
def second_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\nOperations Update\n\nInfrastructure costs fell by 8 percent in March.\n%%EOF"
    )


def wait_for_document_completion(client: TestClient, document_id: str, headers: dict[str, str]) -> dict:
    for _ in range(50):
        payload = client.get(f"/api/v1/documents/{document_id}/status", headers=headers).json()
        if payload["status"] in {"completed", "failed"}:
            return payload
        time.sleep(0.02)
    return client.get(f"/api/v1/documents/{document_id}/status", headers=headers).json()

