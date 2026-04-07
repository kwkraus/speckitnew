from io import BytesIO
from time import perf_counter

from tests.conftest import wait_for_document_completion


def test_full_rag_flow_returns_citations(client, auth_headers, sample_pdf_bytes):
    upload = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("revenue.pdf", BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    document_id = upload.json()["id"]
    wait_for_document_completion(client, document_id, auth_headers)

    conversation = client.post("/api/v1/chat/conversations", headers=auth_headers, json={"title": "Q4"})
    conversation_id = conversation.json()["id"]

    started = perf_counter()
    response = client.post(
        f"/api/v1/chat/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={"content": "What was the quarterly revenue increase?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "15 percent" in payload["assistant_message"]["content"]
    assert payload["assistant_message"]["citations"][0]["document_name"] == "revenue.pdf"
    assert perf_counter() - started < 10

