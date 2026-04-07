# Research: PDF Multi-Agent RAG Workflow

**Phase**: 0 (Research) | **Date**: 2026-04-07

## Research Questions

### RQ-1: Multi-Agent Orchestration Framework

**Question**: Which framework best supports orchestrating multiple specialized AI agents for a document processing pipeline in Python with Azure services?

**Options Evaluated**:

| Framework | Azure Integration | Multi-Agent Support | Complexity | Maturity |
|-----------|-------------------|---------------------|------------|----------|
| Semantic Kernel (Python) | Native (Microsoft) | Agent-based plugins, planners | Medium | Stable (1.x) |
| AutoGen | Good | Agent-to-agent conversation | High | Stable |
| LangChain | SDK-based | Chain composition | Medium | Stable |
| Custom (no framework) | Direct SDK calls | Manual orchestration | Low | N/A |

**Decision**: **Semantic Kernel (Python)** — Microsoft's own orchestration framework with first-class Azure OpenAI and Azure AI Search connectors. Supports the plugin/function-calling pattern which maps cleanly to our three agents (extraction, embedding, indexing). The `Agent` abstraction in SK allows each agent to have its own system prompt, tools, and execution context while the orchestrator coordinates sequencing.

**Rationale**: AutoGen is designed for multi-agent conversation (agents talking to each other) which is overkill — our agents form a linear pipeline, not a collaborative discussion. LangChain would work but requires more glue code for Azure services that SK handles natively. Custom orchestration is viable but loses observability, retry, and state management that SK provides.

**Risk**: Semantic Kernel Python SDK is less mature than the .NET version. Mitigated by: using only stable APIs (agents, plugins, connectors), pinning version, and writing thin wrapper services that can be swapped if needed.

### RQ-2: PDF Extraction Approach

**Question**: What is the best approach for extracting structured content (text, tables, headers) from PDF documents for downstream chunking and embedding?

**Options Evaluated**:

| Approach | Table Support | OCR | Layout Awareness | Cost |
|----------|---------------|-----|------------------|------|
| Azure Document Intelligence | Excellent | Yes | Yes (paragraphs, sections, tables) | Per-page pricing |
| PyPDF2 / pdfplumber | Basic (pdfplumber) | No | Limited | Free |
| Unstructured.io | Good | Via Tesseract | Good | Free (self-hosted) |
| LlamaParse | Good | Yes | Good | Per-page pricing |

**Decision**: **Azure Document Intelligence** (prebuilt-layout model) — best-in-class structured extraction with paragraph, table, and section awareness. Returns content in reading order with bounding boxes, which enables intelligent chunking boundaries.

**Rationale**: PyPDF2 loses structure (no tables, no reading order). Unstructured.io would work but adds Tesseract dependency and has lower accuracy on complex layouts. LlamaParse is comparable quality but adds a non-Azure external dependency. Azure Document Intelligence integrates natively with the Azure ecosystem, supports OCR for scanned PDFs (meeting our edge case requirement), and provides confidence scores for extraction quality.

**Cost consideration**: At ~$1.50 per 1,000 pages, cost is negligible for an internal tool processing hundreds of documents.

### RQ-3: Chunking Strategy

**Question**: How should extracted content be chunked for optimal retrieval in a RAG pipeline?

**Options Evaluated**:

| Strategy | Context Preservation | Implementation | Retrieval Quality |
|----------|---------------------|----------------|-------------------|
| Fixed-size (e.g., 512 tokens) | Low | Simple | Moderate |
| Semantic (paragraph/section boundaries) | High | Medium | High |
| Recursive character splitting | Medium | Simple | Moderate |
| Document Intelligence layout-aware | High | Medium | High |

**Decision**: **Layout-aware semantic chunking** using Document Intelligence's paragraph and section boundaries, with a maximum chunk size of 1,000 tokens and 100-token overlap.

**Rationale**: Fixed-size chunking breaks mid-sentence and loses context. Since Azure Document Intelligence already identifies paragraphs and sections, we can chunk at natural boundaries. The 1,000-token limit ensures chunks fit within embedding model context while preserving enough context for meaningful retrieval. 100-token overlap prevents information loss at boundaries.

**Implementation**: The extraction agent will:
1. Extract content via Document Intelligence (paragraphs + tables)
2. Group consecutive paragraphs under the same section header
3. Split groups exceeding 1,000 tokens at paragraph boundaries
4. Add metadata per chunk: page number, section title, chunk index, source document ID

### RQ-4: Embedding Model Selection

**Question**: Which embedding model should be used for generating vector representations of document chunks?

**Decision**: **Azure OpenAI `text-embedding-3-large`** with 1,536 dimensions.

**Rationale**: Best quality among Azure-hosted models for English text retrieval tasks. The 1,536-dimension configuration balances quality and storage cost (3,072 dimensions is the maximum but doubles index size with marginal quality gain). Native Azure integration means no external API calls.

**Dimensions justification**: Azure AI Search supports up to 3,072 dimensions. Using 1,536 keeps index size manageable while retaining strong retrieval accuracy — benchmarks show <2% quality difference from full 3,072 dimensions on English retrieval tasks.

### RQ-5: Metadata Storage

**Question**: What database should store document metadata, conversation history, and user associations?

**Options Evaluated**:

| Database | Per-User Isolation | Schema Flexibility | Azure Native | Cost (Internal Tool) |
|----------|-------------------|-------------------|--------------|---------------------|
| Azure Cosmos DB (NoSQL) | Partition key | Schemaless JSON | Yes | Serverless tier ~$0 at low scale |
| Azure Database for PostgreSQL | Row-level security | Relational schema | Yes | ~$15/mo minimum |
| Azure SQL Database | Row-level security | Relational schema | Yes | ~$5/mo serverless |
| SQLite (embedded) | File per user | Relational | No | Free |

**Decision**: **Azure Cosmos DB** (NoSQL API) with `user_id` as partition key.

**Rationale**: Per-user data isolation is a core requirement. Cosmos DB's partition key model naturally enforces this — queries within a partition are fast and isolated. Serverless tier has near-zero cost at internal-tool scale (pay per request unit consumed). JSON document model fits our semi-structured data (documents have variable extracted metadata, conversations have variable-length message arrays). No schema migrations needed as the data model evolves.

**Risk**: Cosmos DB query syntax differs from SQL. Mitigated by: thin repository layer that abstracts Cosmos operations behind a Python interface.

### RQ-6: Frontend Framework

**Question**: What frontend framework best suits a conversational chat UI with document management?

**Decision**: **React 18 + TypeScript** with Vite for build tooling.

**Rationale**: React is the most widely adopted framework with mature ecosystem for chat UIs. TypeScript provides type safety that catches API contract mismatches at compile time. Vite provides fast development experience and optimized production builds. MSAL React library provides first-class Azure Entra ID integration.

**UI component approach**: Custom components (not a component library) for maximum flexibility in the chat experience. Minimal dependencies: just React, React Router, and MSAL React. CSS Modules for scoped styling.

### RQ-7: Background Processing Architecture

**Question**: How should the document processing pipeline execute as background work without blocking API requests?

**Options Evaluated**:

| Approach | Resilience | Complexity | Observability | Scale |
|----------|------------|------------|---------------|-------|
| FastAPI BackgroundTasks | Low (lost on restart) | Very low | Manual | Single process |
| Celery + Redis/Service Bus | High (persistent queue) | High | Built-in | Multi-worker |
| In-process asyncio task queue | Medium | Low | Manual | Single process |
| Azure Functions (Durable) | High | Medium | Built-in | Auto-scale |

**Decision**: **In-process asyncio task queue** with status persistence in Cosmos DB.

**Rationale**: For an internal tool with no SLA and ≤10 concurrent jobs, a full distributed task queue (Celery, Durable Functions) is over-engineered. An asyncio-based background task manager within the FastAPI process provides:
- Job submission and status tracking
- Concurrent execution (asyncio.Semaphore for the 10-job limit)
- Status persistence in Cosmos DB (survives reads even if process restarts)
- Simple observability via structured logging

**Risk**: Jobs lost on process restart. Mitigated by: marking documents with `status: processing` in Cosmos DB; on startup, the app scans for stale `processing` documents and re-queues them.

### RQ-8: Duplicate Detection Mechanism

**Question**: How should the system detect duplicate PDF uploads per the spec (FR-018)?

**Decision**: **SHA-256 content hash** computed on upload, stored as a document metadata field, checked per-user before pipeline execution.

**Implementation**:
1. On upload, compute SHA-256 hash of the file bytes
2. Query Cosmos DB: `SELECT * FROM c WHERE c.user_id = @userId AND c.content_hash = @hash`
3. If match found, return a 409 Conflict with the existing document info
4. Frontend displays "duplicate detected" dialog with skip/replace options
5. If user chooses replace: delete old document + index entries, process new file

## Technology Stack Summary

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend framework | FastAPI | 0.115+ |
| Agent orchestration | Semantic Kernel (Python) | 1.x |
| PDF extraction | Azure Document Intelligence | 2024-11-30 API |
| Embeddings | Azure OpenAI text-embedding-3-large | 2024-06-01 API |
| Chat model | Azure OpenAI GPT-4o | 2024-08-06 API |
| Vector search | Azure AI Search | 2024-07-01 API |
| File storage | Azure Blob Storage | v12 SDK |
| Metadata DB | Azure Cosmos DB (NoSQL) | v4 SDK |
| Auth | MSAL Python + Azure Entra ID | 1.x |
| Frontend framework | React + TypeScript | 18.x / 5.5+ |
| Frontend build | Vite | 6.x |
| Frontend auth | MSAL React | 2.x |
| Backend testing | pytest + pytest-asyncio | 8.x |
| Frontend testing | Vitest + React Testing Library | 2.x |
| Linting (Python) | ruff | 0.8+ |
| Linting (TypeScript) | eslint + typescript-eslint | 9.x |
| Formatting (Python) | ruff format | 0.8+ |
| Formatting (TypeScript) | prettier | 3.x |
| Type checking (Python) | mypy | 1.x |
| Containerization | Docker | multi-stage builds |

## Open Questions (Resolved)

All research questions resolved. No remaining unknowns blocking Phase 1 design.
