# API Contract: Documents

**Base path**: `/api/v1/documents`
**Authentication**: Bearer token (Azure Entra ID JWT) required on all endpoints
**User isolation**: All operations scoped to authenticated user's `user_id`

---

## POST /api/v1/documents/upload

Upload a PDF file for processing.

**Request**:
- Content-Type: `multipart/form-data`
- Body:
  - `file` (required): PDF file, max 50 MB

**Response 202** (Accepted):
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "quarterly-report.pdf",
  "status": "pending",
  "file_size": 2456789,
  "created_at": "2026-04-07T10:30:00Z"
}
```

**Response 409** (Conflict — duplicate detected):
```json
{
  "error": "duplicate_document",
  "message": "A document with identical content already exists.",
  "existing_document": {
    "id": "existing-doc-uuid",
    "filename": "quarterly-report-v1.pdf",
    "created_at": "2026-04-01T08:00:00Z"
  }
}
```

**Response 400** (Bad Request):
```json
{
  "error": "invalid_file",
  "message": "File must be a PDF and not exceed 50 MB."
}
```

**Response 401** (Unauthorized):
```json
{
  "error": "unauthorized",
  "message": "Valid authentication token required."
}
```

---

## GET /api/v1/documents

List all documents for the authenticated user.

**Query Parameters**:
- `status` (optional): Filter by status (`pending`, `processing`, `completed`, `failed`)
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20, max: 100): Results per page

**Response 200**:
```json
{
  "documents": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "filename": "quarterly-report.pdf",
      "status": "completed",
      "page_count": 42,
      "chunk_count": 187,
      "file_size": 2456789,
      "created_at": "2026-04-07T10:30:00Z",
      "updated_at": "2026-04-07T10:33:15Z"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20
}
```

---

## GET /api/v1/documents/{document_id}

Get details of a specific document.

**Response 200**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "quarterly-report.pdf",
  "status": "completed",
  "page_count": 42,
  "chunk_count": 187,
  "file_size": 2456789,
  "error_message": null,
  "created_at": "2026-04-07T10:30:00Z",
  "updated_at": "2026-04-07T10:33:15Z"
}
```

**Response 404**:
```json
{
  "error": "not_found",
  "message": "Document not found."
}
```

---

## DELETE /api/v1/documents/{document_id}

Delete a document and all associated index entries.

**Response 202** (Accepted — deletion in progress):
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "deleting",
  "message": "Document and index entries are being removed."
}
```

**Response 404**:
```json
{
  "error": "not_found",
  "message": "Document not found."
}
```

---

## POST /api/v1/documents/{document_id}/replace

Replace a document (used after duplicate detection when user confirms replacement).

**Request**:
- Content-Type: `multipart/form-data`
- Body:
  - `file` (required): PDF file, max 50 MB

**Response 202** (Accepted):
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "quarterly-report-v2.pdf",
  "status": "pending",
  "replaced_document_id": "old-doc-uuid",
  "created_at": "2026-04-07T11:00:00Z"
}
```

---

## GET /api/v1/documents/{document_id}/status

Poll processing status for a document.

**Response 200**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "processing",
  "stage": "embedding",
  "progress": {
    "extraction": "completed",
    "embedding": "in_progress",
    "indexing": "pending"
  },
  "updated_at": "2026-04-07T10:31:45Z"
}
```

**Stage values**: `extraction`, `embedding`, `indexing`
**Stage status values**: `pending`, `in_progress`, `completed`, `failed`

---

## Common Error Responses

All endpoints may return:

**Response 401**:
```json
{
  "error": "unauthorized",
  "message": "Valid authentication token required."
}
```

**Response 500**:
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred. Please try again."
}
```
