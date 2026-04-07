# API Contract: Chat

**Base path**: `/api/v1/chat`
**Authentication**: Bearer token (Azure Entra ID JWT) required on all endpoints
**User isolation**: All operations scoped to authenticated user's `user_id`

---

## POST /api/v1/chat/conversations

Create a new conversation.

**Request**:
```json
{
  "title": "Q4 Revenue Analysis"
}
```

**Response 201**:
```json
{
  "id": "conv-uuid-1234",
  "title": "Q4 Revenue Analysis",
  "created_at": "2026-04-07T10:00:00Z",
  "messages": []
}
```

**Notes**: If `title` is omitted, it will be auto-generated from the first message content.

---

## GET /api/v1/chat/conversations

List all conversations for the authenticated user.

**Query Parameters**:
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20, max: 100): Results per page

**Response 200**:
```json
{
  "conversations": [
    {
      "id": "conv-uuid-1234",
      "title": "Q4 Revenue Analysis",
      "message_count": 8,
      "created_at": "2026-04-07T10:00:00Z",
      "updated_at": "2026-04-07T10:15:30Z"
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 20
}
```

---

## GET /api/v1/chat/conversations/{conversation_id}

Get a conversation with its full message history.

**Response 200**:
```json
{
  "id": "conv-uuid-1234",
  "title": "Q4 Revenue Analysis",
  "created_at": "2026-04-07T10:00:00Z",
  "updated_at": "2026-04-07T10:15:30Z",
  "messages": [
    {
      "id": "msg-uuid-001",
      "role": "user",
      "content": "What were our Q4 revenue figures?",
      "citations": [],
      "created_at": "2026-04-07T10:01:00Z"
    },
    {
      "id": "msg-uuid-002",
      "role": "assistant",
      "content": "Based on the quarterly report, Q4 revenue was $12.3M [1], representing a 15% increase over Q3 [2].",
      "citations": [
        {
          "chunk_id": "doc1_42",
          "document_id": "doc-uuid-1",
          "document_name": "quarterly-report.pdf",
          "page_number": 3,
          "section_title": "Revenue Summary",
          "snippet": "Total Q4 revenue reached $12.3 million, driven primarily by...",
          "relevance": 0.94
        },
        {
          "chunk_id": "doc1_45",
          "document_id": "doc-uuid-1",
          "document_name": "quarterly-report.pdf",
          "page_number": 5,
          "section_title": "Quarter-over-Quarter Growth",
          "snippet": "Comparing to Q3's $10.7M, the 15% growth reflects...",
          "relevance": 0.87
        }
      ],
      "created_at": "2026-04-07T10:01:08Z"
    }
  ]
}
```

---

## POST /api/v1/chat/conversations/{conversation_id}/messages

Send a message and receive an AI-generated response with citations.

**Request**:
```json
{
  "content": "What were our Q4 revenue figures?"
}
```

**Response 200**:
```json
{
  "user_message": {
    "id": "msg-uuid-003",
    "role": "user",
    "content": "What were our Q4 revenue figures?",
    "citations": [],
    "created_at": "2026-04-07T10:01:00Z"
  },
  "assistant_message": {
    "id": "msg-uuid-004",
    "role": "assistant",
    "content": "Based on the quarterly report, Q4 revenue was $12.3M [1], representing a 15% increase over Q3 [2].",
    "citations": [
      {
        "chunk_id": "doc1_42",
        "document_id": "doc-uuid-1",
        "document_name": "quarterly-report.pdf",
        "page_number": 3,
        "section_title": "Revenue Summary",
        "snippet": "Total Q4 revenue reached $12.3 million...",
        "relevance": 0.94
      }
    ],
    "created_at": "2026-04-07T10:01:08Z"
  }
}
```

**Response 400** (no documents indexed):
```json
{
  "error": "no_documents",
  "message": "No documents have been indexed yet. Upload and process at least one document before chatting."
}
```

**Response 400** (empty message):
```json
{
  "error": "invalid_message",
  "message": "Message content cannot be empty."
}
```

**Notes**:
- The response includes BOTH the persisted user message and the generated assistant message
- Citations use bracket notation `[N]` in the response content, mapped to the citations array by index
- Response time target: <10 seconds
- Conversation history (up to last 10 messages) is included as context for the AI model

---

## DELETE /api/v1/chat/conversations/{conversation_id}

Delete a conversation and all its messages.

**Response 204** (No Content)

**Response 404**:
```json
{
  "error": "not_found",
  "message": "Conversation not found."
}
```

---

## GET /api/v1/health

Health check endpoint (no authentication required).

**Response 200**:
```json
{
  "status": "healthy",
  "services": {
    "cosmos_db": "connected",
    "ai_search": "connected",
    "blob_storage": "connected",
    "openai": "connected",
    "document_intelligence": "connected"
  }
}
```

**Response 503** (one or more services unhealthy):
```json
{
  "status": "degraded",
  "services": {
    "cosmos_db": "connected",
    "ai_search": "error",
    "blob_storage": "connected",
    "openai": "connected",
    "document_intelligence": "connected"
  }
}
```

---

## Common Error Responses

All authenticated endpoints may return:

**Response 401**:
```json
{
  "error": "unauthorized",
  "message": "Valid authentication token required."
}
```

**Response 404**:
```json
{
  "error": "not_found",
  "message": "Resource not found."
}
```

**Response 500**:
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred. Please try again."
}
```
