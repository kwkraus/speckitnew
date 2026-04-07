from io import BytesIO

from tests.conftest import wait_for_document_completion


def test_chat_conversation_crud_and_messages(client, auth_headers, sample_pdf_bytes):
    upload = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("report.pdf", BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    document_id = upload.json()["id"]
    wait_for_document_completion(client, document_id, auth_headers)

    created = client.post("/api/v1/chat/conversations", headers=auth_headers, json={"title": "Revenue review"})
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    listing = client.get("/api/v1/chat/conversations", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    message = client.post(
        f"/api/v1/chat/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={"content": "What was Q4 revenue?"},
    )
    assert message.status_code == 200
    assert message.json()["assistant_message"]["citations"]

    detail = client.get(f"/api/v1/chat/conversations/{conversation_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 2

    deleted = client.delete(f"/api/v1/chat/conversations/{conversation_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_chat_guards_empty_message_and_missing_documents(client, auth_headers):
    created = client.post("/api/v1/chat/conversations", headers=auth_headers, json={"title": "Empty index"})
    conversation_id = created.json()["id"]

    no_docs = client.post(
        f"/api/v1/chat/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={"content": "What do we know?"},
    )
    assert no_docs.status_code == 400
    assert no_docs.json()["error"] == "no_documents"

    client.app.state.store.documents["seed"] = {
        "id": "seed",
        "user_id": auth_headers["x-user-id"],
        "filename": "seed.pdf",
        "status": "completed",
        "file_size": 10,
        "blob_url": "memory://pdf-uploads/seed",
        "page_count": 1,
        "chunk_count": 0,
        "error_message": None,
        "progress": {"extraction": "completed", "embedding": "completed", "indexing": "completed"},
        "created_at": client.app.state.store.documents.get("seed", {}).get("created_at"),
        "updated_at": client.app.state.store.documents.get("seed", {}).get("updated_at"),
        "content_hash": "hash",
    }

    empty = client.post(
        f"/api/v1/chat/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={"content": "   "},
    )
    assert empty.status_code == 400
    assert empty.json()["error"] == "invalid_message"

