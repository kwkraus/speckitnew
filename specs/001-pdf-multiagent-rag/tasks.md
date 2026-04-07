# Tasks: PDF Multi-Agent RAG Workflow

**Input**: Design documents from `specs/001-pdf-multiagent-rag/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Included per constitution (Principle II: Tests Define Completion) and plan TDD strategy.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/` (Python FastAPI), `frontend/` (React TypeScript)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency installation, and tooling configuration

- [X] T001 Create backend directory structure with all `__init__.py` files per plan layout in backend/app/ (auth/, models/, api/, services/, agents/) and backend/tests/ (contract/, integration/, unit/)
- [X] T002 [P] Initialize Python project with pyproject.toml (name, version, Python 3.12 requires) and requirements.txt (fastapi, uvicorn, semantic-kernel, msal, azure-ai-formrecognizer, openai, azure-search-documents, azure-storage-blob, azure-cosmos, python-multipart, pydantic-settings, structlog) in backend/
- [X] T003 [P] Initialize React + TypeScript project with Vite, install dependencies (react, react-dom, react-router-dom, @azure/msal-browser, @azure/msal-react) in frontend/ with package.json, tsconfig.json, vite.config.ts, index.html
- [X] T004 [P] Configure ruff linting + formatting and mypy type checking in backend/pyproject.toml (target Python 3.12, line-length 100, strict mypy)
- [X] T005 [P] Configure eslint with typescript-eslint and prettier in frontend/ (eslint.config.js, .prettierrc)
- [X] T006 [P] Configure pytest with pytest-asyncio in backend/pyproject.toml and Vitest with React Testing Library in frontend/vite.config.ts (test section) and frontend/package.json (test script)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Authentication, models, Azure service wrappers, and app shell that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Implement Pydantic Settings configuration class with all Azure service connection fields (Cosmos endpoint/key/db, Blob connection string/container, AI Search endpoint/key/index, OpenAI endpoint/key/deployments, Doc Intelligence endpoint/key, Entra tenant/client IDs, app settings for max file size, max concurrent jobs, chunk sizes) in backend/app/config.py
- [X] T008 Create FastAPI application with CORS middleware (allow frontend origin), lifespan handler for Azure client initialization, and API router registration (/api/v1 prefix) in backend/app/main.py
- [X] T069 Ensure Cosmos DB database and containers exist on startup — verify or create database and containers (`documents` with partition key `/user_id`, `conversations` with partition key `/user_id`) during app lifespan initialization in backend/app/main.py (analogous to T015 `ensure_index_exists` for AI Search)
- [X] T009 [P] Implement Azure Entra ID JWT token validation middleware— decode and validate Bearer tokens against tenant/audience, extract user_id (oid claim) and user_name, reject expired/invalid tokens with 401 in backend/app/auth/middleware.py
- [X] T010 [P] Implement get_current_user FastAPI Depends() function that extracts authenticated user identity from request state (set by auth middleware) and returns a CurrentUser dataclass with user_id and display_name in backend/app/auth/dependencies.py
- [X] T011 [P] Create Document Pydantic models (DocumentCreate, DocumentResponse, DocumentStatus with stage progress dict, DocumentListResponse with pagination) matching data-model.md schema and documents-api.md contract shapes in backend/app/models/document.py
- [X] T012 [P] Create ContentChunk Pydantic model (id, document_id, user_id, chunk_index, content, section_title, page_number, embedding as list[float], token_count) matching data-model.md and AI Search index schema in backend/app/models/chunk.py
- [X] T013 [P] Create Conversation, Message, and Citation Pydantic models (ConversationCreate, ConversationResponse, ConversationListResponse, MessageRequest, MessageResponse with user_message + assistant_message, CitationSchema) matching data-model.md and chat-api.md contracts in backend/app/models/conversation.py
- [X] T014 [P] Implement Azure Blob Storage service — async methods for upload_blob (user_id/doc_id/filename path pattern), delete_blob, and get_blob_url; initialize BlobServiceClient from connection string in backend/app/services/storage_service.py
- [X] T015 [P] Implement Azure AI Search service — async methods for ensure_index_exists (create document-chunks index with HNSW vector config, 1536 dims, cosine), add_documents (batch upload chunks), delete_by_document_id, and hybrid_search (vector + keyword, filtered by user_id, top-K) in backend/app/services/search_service.py
- [X] T016 Implement health check endpoint GET /api/v1/health — check connectivity to Cosmos DB, AI Search, Blob Storage, OpenAI, and Document Intelligence; return service status map with 200 (healthy) or 503 (degraded) in backend/app/api/health.py
- [X] T017 Configure structured logging using structlog with JSON output; add request correlation IDs, log pipeline stage transitions (extraction_started, embedding_complete, indexing_failed etc.) per FR-019 and QR-004 in backend/app/main.py
- [X] T018 Create shared test fixtures — mock Azure Cosmos client, mock Blob client, mock AI Search client, mock OpenAI client, sample PDF bytes fixture, sample user identity fixture, FastAPI TestClient with auth bypass in backend/tests/conftest.py
- [X] T019 [P] Configure MSAL authentication — MsalProvider setup with tenant/client IDs, loginRedirect, acquireTokenSilent for API calls, handleRedirectPromise for callback, logout function in frontend/src/services/auth.ts
- [X] T020 [P] Define TypeScript interfaces for all API request/response shapes (DocumentResponse, DocumentListResponse, DocumentStatusResponse, ConversationResponse, ConversationListResponse, MessageResponse, CitationSchema, HealthResponse, ErrorResponse) matching contracts/ in frontend/src/services/types.ts
- [X] T021 [P] Implement typed API client — fetch wrapper that injects Bearer token from MSAL, sets Content-Type, handles 401 (trigger re-auth), parses JSON responses, supports multipart/form-data for uploads in frontend/src/services/api.ts
- [X] T022 Implement App shell — React Router with routes for / (redirect to chat), /chat (ChatPage), /documents (DocumentsPage), /auth/callback (LoginCallback); wrap in MsalProvider and MsalAuthenticationTemplate to enforce login in frontend/src/App.tsx and frontend/src/main.tsx
- [X] T023 [P] Implement LoginCallback page that handles MSAL redirect response and navigates to /chat on success in frontend/src/pages/LoginCallback.tsx

**Checkpoint**: Foundation ready — authentication, models, Azure service wrappers, and app shell are complete. User story implementation can now begin.

---

## Phase 3: User Story 1 — PDF Document Ingestion & Processing (Priority: P1) 🎯 MVP

**Goal**: Users upload a PDF, and the multi-agent pipeline extracts content, generates embeddings, and indexes chunks in Azure AI Search. Users see processing status updates.

**Independent Test**: Upload a sample PDF, observe status transitions (pending → processing → completed), and verify chunks appear in the search index.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T024 [P] [US1] Write contract tests for POST /api/v1/documents/upload (202 on valid PDF, 400 on non-PDF, 400 on >50MB, 409 on duplicate hash) and GET /api/v1/documents/{id}/status (200 with stage progress) in backend/tests/contract/test_documents_api.py
- [X] T025 [P] [US1] Write integration test for full upload→extract→embed→index pipeline — upload PDF, poll status until completed, verify chunks exist in mock search index with correct embeddings and metadata in backend/tests/integration/test_upload_flow.py
- [X] T026 [P] [US1] Write unit tests for extraction agent — given PDF bytes, returns list of ContentChunk-ready dicts with text, page_number, section_title; test OCR fallback for image PDFs; test error on encrypted PDF in backend/tests/unit/test_extraction_agent.py
- [X] T027 [P] [US1] Write unit tests for embedding agent — given list of text chunks, returns list of 1536-dim float vectors; test batching for large document; test error handling on OpenAI failure in backend/tests/unit/test_embedding_agent.py
- [X] T028 [P] [US1] Write unit tests for indexing agent — given chunks with embeddings, upserts to search index with correct field mapping; test delete_by_document_id; verify user_id is set on all chunks in backend/tests/unit/test_indexing_agent.py
- [X] T029 [P] [US1] Write unit tests for document_service — test create_document (Cosmos write), test duplicate detection by content_hash + user_id, test status transitions (pending→processing→completed|failed), test get_document, test stale job recovery on startup in backend/tests/unit/test_document_service.py
- [X] T040 [P] [US1] Write frontend unit test for UploadPanel — test file selection, validation rejection for non-PDF, upload trigger, duplicate dialog display in frontend/tests/unit/UploadPanel.test.tsx

### Implementation for User Story 1

- [X] T030 [US1] Implement document_service — Cosmos DB CRUD for documents container (create, get, list, update_status), SHA-256 content hash computation, duplicate check query (user_id + content_hash), stale processing recovery (scan for status=processing on startup and re-queue) in backend/app/services/document_service.py
- [X] T031 [P] [US1] Implement extraction agent — call Azure Document Intelligence prebuilt-layout model, parse AnalyzeResult into structured chunks using layout-aware semantic chunking (group by section, split at paragraph boundaries, max 1000 tokens, 100-token overlap), return list of chunk dicts with content/page_number/section_title/token_count in backend/app/agents/extraction.py
- [X] T032 [P] [US1] Implement embedding agent — batch text chunks through Azure OpenAI text-embedding-3-large (1536 dims), handle rate limiting with exponential backoff, return chunks enriched with embedding vectors in backend/app/agents/embedding.py
- [X] T033 [P] [US1] Implement indexing agent — batch upload enriched chunks to Azure AI Search document-chunks index, set all fields per index schema (id, document_id, user_id, content, section_title, page_number, embedding, token_count), update document chunk_count in Cosmos DB in backend/app/agents/indexing.py
- [X] T034 [US1] Implement pipeline orchestrator — asyncio-based task queue with Semaphore(10) for concurrency limit, coordinate extraction→embedding→indexing sequence via Semantic Kernel, update document status/stage in Cosmos DB at each transition, log pipeline events per FR-019, handle per-stage failures gracefully in backend/app/agents/orchestrator.py
- [X] T035 [US1] Implement document API endpoints — POST /upload (validate PDF + size, compute hash, check duplicate → 409 or store in Blob + create Cosmos record + queue pipeline → 202), GET /{id}/status (return stage progress dict), POST /{id}/replace (delete old + re-upload) in backend/app/api/documents.py
- [X] T036 [P] [US1] Create UploadPanel component — drag-and-drop zone with click-to-browse fallback, PDF-only file filter, 50MB size validation with error message, upload progress indicator, duplicate detection dialog (skip/replace options on 409 response) in frontend/src/components/UploadPanel.tsx
- [X] T037 [P] [US1] Create StatusBadge component — colored badge showing document processing status (pending=gray, processing=blue with spinner, completed=green, failed=red with error tooltip) in frontend/src/components/StatusBadge.tsx
- [X] T038 [P] [US1] Create EmptyState component — prompt message with upload CTA when no documents exist, reusable for both documents page and chat page in frontend/src/components/EmptyState.tsx
- [X] T039 [US1] Implement useDocuments hook — fetch document list, upload file with progress callback, poll status for processing documents (5s interval), handle duplicate 409 response, delete document in frontend/src/hooks/useDocuments.ts

**Checkpoint**: User Story 1 complete — PDFs can be uploaded, processed through the 3-agent pipeline, and indexed in Azure AI Search. Status is visible. This is the independently testable MVP foundation.

---

## Phase 4: User Story 2 — Natural Language Chat with Indexed Documents (Priority: P1)

**Goal**: Users ask natural language questions about their documents and receive cited answers via a conversational chat interface with multi-turn context.

**Independent Test**: With pre-indexed documents, submit a question through the chat UI and receive a relevant answer with citations linking to source documents and pages.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T041 [P] [US2] Write contract tests for POST /api/v1/chat/conversations (201), GET /conversations (200 with pagination), GET /conversations/{id} (200 with messages), POST /conversations/{id}/messages (200 with user_message + assistant_message + citations), DELETE /conversations/{id} (204), 400 on empty message, 400 when no documents indexed in backend/tests/contract/test_chat_api.py
- [X] T042 [P] [US2] Write integration test for full RAG flow — seed search index with sample chunks, send question, verify response contains relevant content and valid citations referencing seeded documents in backend/tests/integration/test_chat_flow.py
- [X] T043 [P] [US2] Write unit tests for chat_service — test query embedding generation, test hybrid search call with user_id filter, test prompt construction with context + conversation history (last 10 messages), test citation extraction from model response, test "no relevant results" handling, test empty index guard in backend/tests/unit/test_chat_service.py
- [X] T051 [P] [US2] Write frontend unit test for ChatPanel — test message rendering, test send message trigger, test loading state display, test empty state, test citation link click behavior in frontend/tests/unit/ChatPanel.test.tsx

### Implementation for User Story 2

- [X] T044 [US2] Implement chat_service — RAG query pipeline: generate query embedding (Azure OpenAI), execute hybrid search in AI Search (vector + keyword, filter by user_id, top-5), construct system prompt with retrieved chunks as context + last 10 messages for conversation history, call GPT-4o for answer generation with citation instructions, parse [N] citation references from response and map to source chunks, return no-answer response when search returns no relevant results (FR-011) in backend/app/services/chat_service.py
- [X] T045 [US2] Implement chat API endpoints — POST /conversations (create with optional title, auto-generate from first message if omitted), GET /conversations (list with pagination, user_id filter), GET /conversations/{id} (full conversation with embedded messages), POST /conversations/{id}/messages (validate non-empty content, guard against empty index with 400, call chat_service, persist both messages to Cosmos, return MessageResponse), DELETE /conversations/{id} (remove conversation doc from Cosmos, return 204) in backend/app/api/chat.py
- [X] T046 [P] [US2] Create MessageBubble component — user messages right-aligned (blue), assistant messages left-aligned (gray), render citation markers as clickable [N] links that scroll to CitationCard, show timestamp, render markdown formatting in assistant messages in frontend/src/components/MessageBubble.tsx
- [X] T047 [P] [US2] Create CitationCard component — expandable card showing document_name, page_number, section_title, snippet text, relevance score as percentage; collapsed by default, expand on citation link click in frontend/src/components/CitationCard.tsx
- [X] T048 [US2] Create ChatPanel component — scrollable message list (auto-scroll to bottom on new message), text input with send button and Enter-key submit, loading skeleton during AI response generation, empty state when no messages, citation cards section below messages in frontend/src/components/ChatPanel.tsx
- [X] T049 [US2] Implement useChat hook — manage conversation list, active conversation selection, message sending (optimistic user message display + API call + append assistant response), create new conversation, delete conversation, handle loading/error states in frontend/src/hooks/useChat.ts
- [X] T050 [US2] Create ChatPage — two-column layout with conversation list sidebar (left) and active chat panel (right), new conversation button, document count indicator, empty state when no conversations, responsive layout in frontend/src/pages/ChatPage.tsx

**Checkpoint**: User Stories 1 AND 2 complete — the full end-to-end RAG experience works (upload → process → chat with citations). This is the complete P1 MVP.

---

## Phase 5: User Story 3 — Document Library Management (Priority: P2)

**Goal**: Users view all uploaded documents with status, and can delete documents which cascades to removing index entries and blob files.

**Independent Test**: With multiple documents uploaded, view the library listing showing names/dates/status. Delete one document and confirm its content no longer appears in chat answers.

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T052 [P] [US3] Write contract tests for GET /api/v1/documents (200 with pagination and status filter) and DELETE /api/v1/documents/{id} (202 with deletion confirmation, 404 for missing) in backend/tests/contract/test_documents_api.py (extends test file from T024)
- [X] T058 [P] [US3] Write frontend unit test for DocumentLibrary — test table rendering with sample data, test delete confirmation dialog, test status filter, test empty state in frontend/tests/unit/DocumentLibrary.test.tsx

### Implementation for User Story 3

- [X] T053 [US3] Implement document list endpoint GET /api/v1/documents with pagination (page, page_size), optional status filter, ordered by created_at desc, scoped to user_id in backend/app/api/documents.py
- [X] T054 [US3] Implement document detail endpoint GET /api/v1/documents/{id} with user_id ownership check, 404 on missing in backend/app/api/documents.py
- [X] T055 [US3] Implement cascading delete — DELETE /api/v1/documents/{id} triggers: delete chunks from AI Search by document_id → delete blob from storage → delete Cosmos DB record; return 202; handle partial failures gracefully with logging in backend/app/api/documents.py and backend/app/services/document_service.py
- [X] T056 [US3] Create DocumentLibrary component — sortable table with columns (filename, status via StatusBadge, page count, upload date, actions), delete button with confirmation dialog, status filter dropdown, pagination controls in frontend/src/components/DocumentLibrary.tsx
- [X] T057 [US3] Create DocumentsPage — full-width layout with DocumentLibrary, upload button linking to UploadPanel modal, document count header in frontend/src/pages/DocumentsPage.tsx

**Checkpoint**: User Stories 1, 2, AND 3 complete — full document lifecycle (upload, process, query, manage, delete) is working.

---

## Phase 6: User Story 4 — Batch Document Upload (Priority: P3)

**Goal**: Users upload multiple PDFs at once; each processes independently with per-file status tracking and error isolation.

**Independent Test**: Upload 5 PDFs simultaneously, confirm all 5 process independently. If one fails, the other 4 complete successfully.

### Tests for User Story 4 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T059 [P] [US4] Write contract test for multi-file upload — POST /api/v1/documents/upload with multiple files returns list of document responses, each with independent status in backend/tests/contract/test_documents_api.py (extends test file from T024)

### Implementation for User Story 4

- [X] T060 [US4] Extend POST /api/v1/documents/upload to accept multiple files (List[UploadFile]) — validate each independently (PDF type, size limit), check duplicates per file, return list of DocumentResponse objects, queue each for independent pipeline processing in backend/app/api/documents.py
- [X] T061 [US4] Update UploadPanel to support multi-file selection — show per-file upload status list with individual StatusBadge, allow removing files before submission, show per-file duplicate detection dialogs in frontend/src/components/UploadPanel.tsx
- [X] T062 [US4] Verify per-document error isolation in orchestrator — one document failure must not affect other queued documents; add error boundary per pipeline invocation in backend/app/agents/orchestrator.py

**Checkpoint**: All user stories (1–4) complete — the system supports single and batch uploads, chat with citations, and full document lifecycle management.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Deployment artifacts, consistency verification, and performance validation

- [X] T063 [P] Create backend Dockerfile — multi-stage build (builder + runtime), Python 3.12-slim base, install requirements, copy app, expose port 8000, CMD uvicorn in backend/Dockerfile
- [X] T064 [P] Create frontend Dockerfile — multi-stage build (builder with Node 20 + runtime with nginx), npm ci + npm run build, copy dist to nginx, configure SPA fallback in frontend/Dockerfile
- [X] T065 Cross-story UX consistency review — verify all pages have consistent loading indicators, error toasts, empty states, and accessible navigation; verify keyboard navigation works across ChatPage, DocumentsPage, and upload flows; execute manual first-attempt walkthrough per SC-004 (upload → index → chat → manage lifecycle) without consulting documentation
- [X] T066 Performance budget verification — measure and assert: query response <10s (integration test), PDF processing <3min for 50-page sample (integration test timing), delete propagation <30s (integration test), 10 concurrent jobs without >20% degradation
- [X] T067 [P] Add structured logging verification — confirm all pipeline stages emit expected log events (extraction_started, extraction_completed, embedding_started, etc.) with correlation IDs; verify logs are parseable JSON per FR-019
- [X] T068 Run quickstart.md validation — follow setup instructions in specs/001-pdf-multiagent-rag/quickstart.md against actual project, verify backend starts, frontend builds, and end-to-end flow works
- [X] T070 RAG quality evaluation — create curated test dataset with known-answer questions and unanswerable questions; verify citation accuracy ≥90% against ground truth (SC-003) and unanswerable question detection ≥95% (SC-005) using automated evaluation script in backend/tests/evaluation/test_rag_quality.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — this is the MVP
- **User Story 2 (Phase 4)**: Depends on Foundational — can run in parallel with US1 (backend independent), but ChatPage benefits from US1's UploadPanel and StatusBadge
- **User Story 3 (Phase 5)**: Depends on Foundational — uses document endpoints started in US1
- **User Story 4 (Phase 6)**: Depends on US1 (extends upload endpoint and orchestrator)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational — no dependencies on other stories
- **User Story 2 (P1)**: After Foundational — no dependencies on other stories (can use pre-seeded index for testing)
- **User Story 3 (P2)**: After Foundational — no dependencies on other stories (uses Document model from Foundational)
- **User Story 4 (P3)**: After US1 — extends upload endpoint and orchestrator created in US1

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/services before API endpoints
- Backend endpoints before frontend components
- Hooks before pages (hooks provide data to pages)
- Frontend unit tests validate component behavior alongside implementation and remain green as components evolve

### Parallel Opportunities

- All Setup tasks T002–T006 marked [P] can run simultaneously
- Foundational tasks T009–T015 and T019–T023 marked [P] can run simultaneously
- Within US1: Tests T024–T029, T040 can run in parallel; agents T031–T033 can run in parallel; frontend components T036–T038 can run in parallel
- Within US2: Tests T041–T043, T051 can run in parallel; components T046–T047 can run in parallel
- US1 and US2 can be worked on in parallel by different developers after Foundational phase
- US3 can run in parallel with US1/US2

---

## Parallel Example: User Story 1

```text
# Write all tests in parallel:
T024: Contract tests for upload/status endpoints
T025: Integration test for upload→index pipeline
T026: Unit test for extraction agent
T027: Unit test for embedding agent
T028: Unit test for indexing agent
T029: Unit test for document_service
T040: Frontend unit test for UploadPanel

# Implement all three agents in parallel(different files):
T031: Extraction agent in agents/extraction.py
T032: Embedding agent in agents/embedding.py
T033: Indexing agent in agents/indexing.py

# Create frontend components in parallel (different files):
T036: UploadPanel in components/UploadPanel.tsx
T037: StatusBadge in components/StatusBadge.tsx
T038: EmptyState in components/EmptyState.tsx
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (upload + process pipeline)
4. **STOP and VALIDATE**: Upload a PDF, verify it processes and appears in search index
5. Complete Phase 4: User Story 2 (chat with citations)
6. **STOP and VALIDATE**: Ask a question, verify relevant cited answer
7. Deploy/demo P1 MVP

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Upload pipeline works
3. Add User Story 2 → Test independently → Full RAG chat works (**MVP!**)
4. Add User Story 3 → Test independently → Document management works
5. Add User Story 4 → Test independently → Batch upload works
6. Polish → Performance verified, Docker images ready

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (backend agents + upload API)
   - Developer B: User Story 2 (backend chat + frontend chat UI)
   - Developer C: User Story 3 (document library frontend)
3. After US1 done: Developer A picks up User Story 4
4. After all stories: Team does Polish together

---

## Notes

- [P] tasks = different files, no cross-dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing (TDD red-green-refactor)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

