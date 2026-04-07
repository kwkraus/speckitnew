# Implementation Plan: PDF Multi-Agent RAG Workflow

**Branch**: `001-pdf-multiagent-rag` | **Date**: 2026-04-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-pdf-multiagent-rag/spec.md`

## Summary

Build a multi-agent document processing pipeline that ingests PDF files, extracts structured content via Azure Document Intelligence, generates vector embeddings via Azure OpenAI, stores them in Azure AI Search, and exposes a conversational chat UI for natural language querying with source citations. The system uses Semantic Kernel to orchestrate three specialized agents (extraction, embedding, indexing) as a coordinated background pipeline. A React+TypeScript frontend provides document management and chat. Authentication is enforced via Azure Entra ID with per-user data isolation.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**: FastAPI, Semantic Kernel (Python), MSAL, Azure Document Intelligence SDK, Azure OpenAI SDK, Azure AI Search SDK, Azure Blob Storage SDK, Azure Cosmos DB SDK; React 18, Vite, MSAL React
**Storage**: Azure Cosmos DB (document metadata, conversations), Azure Blob Storage (PDF files), Azure AI Search (vector index)
**Testing**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend)
**Target Platform**: Azure cloud — Azure App Service (backend), Azure Static Web Apps (frontend)
**Project Type**: Web application (API backend + SPA frontend + background agent pipeline)
**Performance Goals**: <10s query response time, <3 min processing for 50-page PDFs, 10 concurrent processing jobs
**Constraints**: Per-user data isolation enforced at all storage layers, 50 MB max file size, English-only documents, no formal SLA
**Scale/Scope**: Internal tool for knowledge workers, moderate scale (~tens of concurrent users, hundreds of documents per user)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Quality** ✅: Linting via `ruff` (Python) and `eslint` (TypeScript). Formatting via `ruff format` (Python) and `prettier` (TypeScript). Type checking via `mypy` (Python) and `tsc --noEmit` (TypeScript). All enforced in CI before merge.
- **Testing** ✅: Each user story has an independent test described in the spec. Test strategy: contract tests validate API endpoint schemas and response shapes; integration tests verify full upload→index→query flows per story; unit tests cover each agent independently with mocked Azure dependencies. Tests are written before implementation (TDD red-green-refactor).
- **UX Consistency** ✅: Chat interface follows standard conversational patterns (user right-aligned, assistant left-aligned, loading skeleton during generation). Citations rendered inline with expandable detail cards. Document library uses standard table layout with status badges. Empty states, error states, and loading states are defined per component. Accessibility: semantic HTML, ARIA labels for interactive elements, keyboard navigation support.
- **Performance** ✅: Budgets defined — query response <10s (measured via integration test timing assertions), PDF processing <3 min for ≤50 pages (measured via pipeline timing in integration tests), document deletion propagation <30s (measured via search query after delete). Concurrent processing target: 10 jobs with ≤20% degradation (load test in staging).

## Project Structure

### Documentation (this feature)

```text
specs/001-pdf-multiagent-rag/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── documents-api.md
│   └── chat-api.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry, CORS, lifespan
│   ├── config.py                # Pydantic settings (env-based config)
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── middleware.py        # Azure Entra ID token validation
│   │   └── dependencies.py     # FastAPI Depends() for current user
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py          # Document metadata model
│   │   ├── conversation.py      # Conversation + Message models
│   │   └── chunk.py             # Content chunk model
│   ├── api/
│   │   ├── __init__.py
│   │   ├── documents.py         # Upload, list, delete, status endpoints
│   │   ├── chat.py              # Send message, get conversation endpoints
│   │   └── health.py            # Health check endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_service.py  # Document CRUD + duplicate detection
│   │   ├── chat_service.py      # RAG query orchestration
│   │   ├── search_service.py    # Azure AI Search client wrapper
│   │   └── storage_service.py   # Azure Blob Storage client wrapper
│   └── agents/
│       ├── __init__.py
│       ├── orchestrator.py      # Semantic Kernel pipeline orchestrator
│       ├── extraction.py        # PDF extraction agent (Document Intelligence)
│       ├── embedding.py         # Embedding generation agent (Azure OpenAI)
│       └── indexing.py          # Vector index agent (Azure AI Search)
├── tests/
│   ├── conftest.py              # Shared fixtures, mocks
│   ├── contract/
│   │   ├── test_documents_api.py
│   │   └── test_chat_api.py
│   ├── integration/
│   │   ├── test_upload_flow.py  # US1: upload → extract → embed → index
│   │   └── test_chat_flow.py   # US2: question → search → answer + citations
│   └── unit/
│       ├── test_extraction_agent.py
│       ├── test_embedding_agent.py
│       ├── test_indexing_agent.py
│       ├── test_chat_service.py
│       └── test_document_service.py
├── requirements.txt
├── pyproject.toml
└── Dockerfile

frontend/
├── src/
│   ├── components/
│   │   ├── ChatPanel.tsx        # Chat message list + input
│   │   ├── MessageBubble.tsx    # Single message with citation links
│   │   ├── CitationCard.tsx     # Expandable citation detail
│   │   ├── DocumentLibrary.tsx  # Document table with status
│   │   ├── UploadPanel.tsx      # Drag-and-drop file upload
│   │   ├── StatusBadge.tsx      # Processing status indicator
│   │   └── EmptyState.tsx       # Empty state prompts
│   ├── pages/
│   │   ├── ChatPage.tsx         # Main chat + document sidebar layout
│   │   ├── DocumentsPage.tsx    # Full document library view
│   │   └── LoginCallback.tsx    # MSAL auth redirect handler
│   ├── services/
│   │   ├── api.ts               # Typed API client (fetch wrapper)
│   │   ├── auth.ts              # MSAL configuration + token acquisition
│   │   └── types.ts             # Shared TypeScript interfaces
│   ├── hooks/
│   │   ├── useChat.ts           # Chat state + message sending
│   │   └── useDocuments.ts      # Document list + polling
│   ├── App.tsx                  # Router + auth provider
│   └── main.tsx                 # Entry point
├── tests/
│   └── unit/
│       ├── ChatPanel.test.tsx
│       ├── DocumentLibrary.test.tsx
│       └── UploadPanel.test.tsx
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── Dockerfile
```

**Structure Decision**: Web application with separate frontend and backend projects. The backend hosts the API and agent pipeline in a single Python process (FastAPI with background tasks). The frontend is a React SPA served independently. This separation enables independent deployment, testing, and scaling while keeping the agent orchestration co-located with the API for simplicity (no distributed message bus needed for an internal tool).

**Service Wrapper Pattern**: Azure Blob Storage and Azure AI Search have dedicated service wrappers (`storage_service.py`, `search_service.py`) because they expose generic operations (upload/delete blob, upsert/search/delete index docs) reused across multiple features. Cosmos DB operations are embedded directly in domain services (`document_service.py`, chat API) because each domain has distinct query patterns, partition key logic, and data shaping — a generic Cosmos wrapper would add indirection without reducing complexity.

## Complexity Tracking

No constitution violations. All four gates pass without exceptions.
