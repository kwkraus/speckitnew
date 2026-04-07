from io import BytesIO
from time import perf_counter

from tests.conftest import wait_for_document_completion


def test_full_upload_extract_embed_index_pipeline(client, auth_headers, sample_pdf_bytes, capsys):
    started = perf_counter()
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("quarterly-report.pdf", BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 202

    document_id = response.json()["id"]
    status_payload = wait_for_document_completion(client, document_id, auth_headers)
    assert status_payload["status"] == "completed"

    stored_chunks = [
        chunk for chunk in client.app.state.store.chunks.values() if chunk["document_id"] == document_id
    ]
    assert stored_chunks
    assert all(chunk["user_id"] == auth_headers["x-user-id"] for chunk in stored_chunks)
    assert all(len(chunk["embedding"]) == 1536 for chunk in stored_chunks)
    assert perf_counter() - started < 10

    captured = capsys.readouterr().out
    assert "extraction_started" in captured
    assert "indexing_completed" in captured

