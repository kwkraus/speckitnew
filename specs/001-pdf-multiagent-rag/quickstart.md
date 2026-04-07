# Quickstart: PDF Multi-Agent RAG Workflow

## Prerequisites

- Python 3.12+
- Node.js 20+
- Azure subscription with the following services provisioned:
  - Azure Cosmos DB (NoSQL API, serverless tier)
  - Azure Blob Storage
  - Azure AI Search (Basic tier or higher for vector search)
  - Azure OpenAI (with `text-embedding-3-large` and `gpt-4o` deployments)
  - Azure Document Intelligence
  - Azure Entra ID app registration (for authentication)

## Environment Setup

### 1. Clone and install

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Configure environment variables

Create `backend/.env`:

```env
# Azure Entra ID
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>

# Azure Cosmos DB
COSMOS_ENDPOINT=https://<account>.documents.azure.com:443/
COSMOS_DATABASE=pdf-rag
COSMOS_KEY=<your-key>

# Azure Blob Storage
BLOB_CONNECTION_STRING=<your-connection-string>
BLOB_CONTAINER=pdf-uploads

# Azure AI Search
SEARCH_ENDPOINT=https://<service>.search.windows.net
SEARCH_API_KEY=<your-key>
SEARCH_INDEX_NAME=document-chunks

# Azure OpenAI
OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
OPENAI_API_KEY=<your-key>
OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
OPENAI_CHAT_DEPLOYMENT=gpt-4o

# Azure Document Intelligence
DOC_INTELLIGENCE_ENDPOINT=https://<resource>.cognitiveservices.azure.com/
DOC_INTELLIGENCE_KEY=<your-key>

# App settings
MAX_FILE_SIZE_MB=50
MAX_CONCURRENT_JOBS=10
CHUNK_MAX_TOKENS=1000
CHUNK_OVERLAP_TOKENS=100
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_AZURE_CLIENT_ID=<your-client-id>
VITE_AZURE_TENANT_ID=<your-tenant-id>
VITE_AZURE_REDIRECT_URI=http://localhost:5173/auth/callback
```

### 3. Run locally

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Usage

### Upload a document

1. Sign in via the Azure Entra ID login prompt
2. Navigate to the Documents page
3. Drag and drop a PDF file (or click to browse)
4. Observe the processing status: pending → extraction → embedding → indexing → completed

### Chat with your documents

1. Navigate to the Chat page
2. Type a natural language question about your uploaded documents
3. Receive an AI-generated answer with numbered citations
4. Click citation numbers to see source details (document name, page, excerpt)

### Manage documents

- View all documents and their processing status on the Documents page
- Delete documents to remove them and their index entries
- Re-upload updated versions of documents (duplicate detection will prompt skip/replace)

## Running Tests

```bash
# Backend tests
cd backend
pytest                           # All tests
pytest tests/contract/           # Contract tests only
pytest tests/unit/               # Unit tests only
pytest tests/integration/        # Integration tests only
pytest -k "US1"                  # Tests for User Story 1

# Frontend tests
cd frontend
npm test                         # All tests
npm test -- --reporter=verbose   # Verbose output
```

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/documents/upload` | POST | Upload a PDF for processing |
| `/api/v1/documents` | GET | List all documents |
| `/api/v1/documents/{id}` | GET | Get document details |
| `/api/v1/documents/{id}` | DELETE | Delete document + index entries |
| `/api/v1/documents/{id}/status` | GET | Poll processing status |
| `/api/v1/documents/{id}/replace` | POST | Replace duplicate document |
| `/api/v1/chat/conversations` | POST | Create a conversation |
| `/api/v1/chat/conversations` | GET | List conversations |
| `/api/v1/chat/conversations/{id}` | GET | Get conversation with messages |
| `/api/v1/chat/conversations/{id}/messages` | POST | Send message, get AI response |
| `/api/v1/chat/conversations/{id}` | DELETE | Delete conversation |
| `/api/v1/health` | GET | Health check (no auth) |

See `specs/001-pdf-multiagent-rag/contracts/` for full request/response schemas.

## Architecture Overview

```
┌──────────────┐     REST API      ┌──────────────────────────┐
│   React SPA  │ ───────────────── │    FastAPI Backend       │
│   (Vite)     │                   │                          │
│              │                   │  ┌─── Auth (MSAL) ────┐  │
│  • Chat UI   │                   │  │ Token validation   │  │
│  • Doc Mgmt  │                   │  └────────────────────┘  │
│  • Upload    │                   │                          │
└──────────────┘                   │  ┌── Agent Pipeline ──┐  │
                                   │  │ Semantic Kernel     │  │
                                   │  │ • Extraction Agent  │──── Azure Doc Intelligence
                                   │  │ • Embedding Agent   │──── Azure OpenAI
                                   │  │ • Indexing Agent    │──── Azure AI Search
                                   │  └────────────────────┘  │
                                   │                          │
                                   │  ┌── Chat Service ────┐  │
                                   │  │ • Query embedding   │──── Azure OpenAI
                                   │  │ • Vector search     │──── Azure AI Search
                                   │  │ • Response + cites  │──── Azure OpenAI (GPT-4o)
                                   │  └────────────────────┘  │
                                   └──────────────────────────┘
                                              │
                                   ┌──────────┼──────────┐
                                   │          │          │
                              Cosmos DB   Blob Store  AI Search
                              (metadata)  (PDFs)      (vectors)
```
