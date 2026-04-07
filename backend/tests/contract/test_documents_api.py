from io import BytesIO

from tests.conftest import wait_for_document_completion


def test_upload_accepts_pdf(client, auth_headers, sample_pdf_bytes):
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("quarterly-report.pdf", BytesIO(sample_pdf_bytes), "application/pdf")},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["filename"] == "quarterly-report.pdf"
    assert payload["status"] in {"pending", "processing"}


def test_upload_rejects_non_pdf(client, auth_headers):
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("notes.txt", BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_file"


def test_upload_detects_duplicate(client, auth_headers, sample_pdf_bytes):
    files = {"file": ("report.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
    first = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    second = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)

    assert first.status_code == 202
    assert second.status_code == 409
    assert second.json()["error"] == "duplicate_document"


def test_document_status_and_delete_flow(client, auth_headers, sample_pdf_bytes):
    upload = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("report.pdf", BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    document_id = upload.json()["id"]

    status_payload = wait_for_document_completion(client, document_id, auth_headers)
    assert status_payload["status"] == "completed"
    assert status_payload["progress"]["indexing"] == "completed"

    list_response = client.get("/api/v1/documents?status=completed", headers=auth_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    delete_response = client.delete(f"/api/v1/documents/{document_id}", headers=auth_headers)
    assert delete_response.status_code == 202
    assert delete_response.json()["status"] == "deleting"
    assert all(chunk["document_id"] != document_id for chunk in client.app.state.store.chunks.values())


def test_multi_file_upload_returns_independent_results(client, auth_headers, sample_pdf_bytes, second_pdf_bytes):
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files=[
            ("file", ("report-a.pdf", BytesIO(sample_pdf_bytes), "application/pdf")),
            ("file", ("report-b.pdf", BytesIO(second_pdf_bytes), "application/pdf")),
        ],
    )

    assert response.status_code == 202
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == 2

