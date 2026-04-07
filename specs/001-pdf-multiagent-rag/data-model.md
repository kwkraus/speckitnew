# Data Model: PDF Multi-Agent RAG Workflow

**Phase**: 1 (Design) | **Date**: 2026-04-07 | **Spec entities**: Document, Content Chunk, Conversation, Message, Citation, Index Entry

## Entity Definitions

### Document

Represents an uploaded PDF file and its processing state.

```
Document {
  id:            string (UUID v4, primary key)
  user_id:       string (Azure Entra ID object ID, partition key)
  filename:      string (original upload filename)
  content_hash:  string (SHA-256 hex digest of file bytes)
  blob_url:      string (Azure Blob Storage URL)
  status:        enum { pending, processing, completed, failed }
  page_count:    integer (null until extraction completes)
  chunk_count:   integer (null until indexing completes)
  error_message: string (null unless status = failed)
  file_size:     integer (bytes)
  created_at:    datetime (UTC, ISO 8601)
  updated_at:    datetime (UTC, ISO 8601)
}
```

**Storage**: Azure Cosmos DB, container `documents`, partition key `/user_id`
**Constraints**:
- `content_hash` + `user_id` must be unique (enforced at application layer)
- `file_size` ≤ 52,428,800 bytes (50 MB)
- `filename` must end with `.pdf`
- `status` transitions: pending → processing → completed | failed

### Content Chunk

Represents a segment of extracted text from a document, stored in the vector index.

```
ContentChunk {
  id:               string (format: "{document_id}_{chunk_index}")
  document_id:      string (FK → Document.id)
  user_id:          string (denormalized for search filtering)
  chunk_index:      integer (0-based position within document)
  content:          string (extracted text, ≤1000 tokens)
  section_title:    string (nullable, heading from PDF structure)
  page_number:      integer (1-based source page)
  embedding:        float[] (1536 dimensions, text-embedding-3-large)
  token_count:      integer (number of tokens in content)
  created_at:       datetime (UTC, ISO 8601)
}
```

**Storage**: Azure AI Search index `document-chunks`
**Index configuration**:
- `id`: filterable, retrievable (key field)
- `document_id`: filterable, retrievable
- `user_id`: filterable (required in every query for isolation)
- `content`: searchable, retrievable
- `section_title`: searchable, retrievable, filterable
- `page_number`: retrievable, sortable
- `embedding`: searchable (vector, HNSW algorithm, cosine similarity)
- `token_count`: retrievable

### Conversation

Represents a chat session scoped to a user.

```
Conversation {
  id:          string (UUID v4, primary key)
  user_id:     string (Azure Entra ID object ID, partition key)
  title:       string (auto-generated from first message, max 100 chars)
  created_at:  datetime (UTC, ISO 8601)
  updated_at:  datetime (UTC, ISO 8601)
}
```

**Storage**: Azure Cosmos DB, container `conversations`, partition key `/user_id`

### Message

Represents a single message in a conversation (user question or assistant response).

```
Message {
  id:              string (UUID v4)
  conversation_id: string (FK → Conversation.id)
  user_id:         string (partition key, denormalized)
  role:            enum { user, assistant }
  content:         string (message text)
  citations:       Citation[] (empty for user messages)
  created_at:      datetime (UTC, ISO 8601)
}
```

**Storage**: Azure Cosmos DB, embedded within the `conversations` container as sub-documents. Messages are stored in a `messages` array within the Conversation document to enable atomic reads of full conversation history.

**Design note**: Embedding messages within the Conversation document (rather than a separate container) keeps conversation reads as single-document lookups. Given session-scoped history and moderate message counts, document size will stay well within Cosmos DB's 2 MB limit.

### Citation

Represents a reference from an assistant message back to a source chunk.

```
Citation {
  chunk_id:       string (FK → ContentChunk.id)
  document_id:    string (FK → Document.id)
  document_name:  string (denormalized filename for display)
  page_number:    integer (source page)
  section_title:  string (nullable)
  snippet:        string (relevant excerpt from chunk, max 200 chars)
  relevance:      float (0.0–1.0, search score normalized)
}
```

**Storage**: Inline within Message.citations array (no separate storage).

### Index Entry (Logical)

The Index Entry entity from the spec maps directly to the ContentChunk stored in Azure AI Search. There is no separate "index entry" — the chunk IS the index entry. The search index schema above defines all fields needed for retrieval.

## Entity Relationships

```
User (Azure Entra ID)
  │
  ├── 1:N → Document
  │           │
  │           └── 1:N → ContentChunk (in Azure AI Search)
  │
  └── 1:N → Conversation
              │
              └── 1:N → Message (embedded in Conversation doc)
                          │
                          └── 0:N → Citation (embedded in Message)
                                      │
                                      └── → ContentChunk (reference)
```

## Storage Layout

### Cosmos DB Containers

| Container | Partition Key | Typical Document Size | RU Estimate (per op) |
|-----------|---------------|----------------------|---------------------|
| `documents` | `/user_id` | ~1 KB | 5 RU read, 10 RU write |
| `conversations` | `/user_id` | ~5-50 KB (with messages) | 10 RU read, 15 RU write |

### Azure AI Search Index

| Index Name | Key Field | Vector Config | Estimated Docs |
|------------|-----------|---------------|----------------|
| `document-chunks` | `id` | HNSW, cosine, 1536 dims | ~500 chunks/doc × N docs |

### Azure Blob Storage

| Container | Path Pattern | Retention |
|-----------|-------------|-----------|
| `pdf-uploads` | `{user_id}/{document_id}/{filename}` | Until document deleted |

## Data Flow

### Upload Pipeline
```
PDF file → Blob Storage (pdf-uploads/{user_id}/{doc_id}/{name})
         → Cosmos DB (documents: status=pending)
         → Extraction Agent → raw text + structure
         → Embedding Agent → 1536-dim vectors per chunk
         → Indexing Agent → Azure AI Search (document-chunks index)
         → Cosmos DB (documents: status=completed)
```

### Query Pipeline
```
User question → Embedding Agent → query vector (1536 dims)
             → Azure AI Search (hybrid: vector + keyword, filtered by user_id)
             → Top-K chunks retrieved (K=5 default)
             → Chat model (GPT-4o) with context + conversation history
             → Response with inline citations
             → Cosmos DB (conversation: append message)
```

### Delete Pipeline
```
Delete request → Cosmos DB (documents: mark deleted)
              → Azure AI Search (delete chunks where document_id = X)
              → Blob Storage (delete blob)
              → Cosmos DB (documents: remove record)
```
