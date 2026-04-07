from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agents.embedding import EmbeddingAgent
from app.agents.extraction import ExtractionAgent
from app.agents.indexing import IndexingAgent
from app.agents.orchestrator import PipelineOrchestrator
from app.api import chat, documents, health
from app.auth.middleware import AuthMiddleware
from app.config import get_settings
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.services.runtime_store import RuntimeStore
from app.services.search_service import SearchService
from app.services.storage_service import StorageService


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ]
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    store = RuntimeStore()
    storage_service = StorageService(settings, store)
    search_service = SearchService(settings, store)
    document_service = DocumentService(store, storage_service, search_service)
    chat_service = ChatService(store, search_service)
    extraction_agent = ExtractionAgent(settings)
    embedding_agent = EmbeddingAgent()
    indexing_agent = IndexingAgent(search_service)
    orchestrator = PipelineOrchestrator(
        document_service,
        storage_service,
        extraction_agent,
        embedding_agent,
        indexing_agent,
        max_concurrent_jobs=settings.max_concurrent_jobs,
    )

    app.state.settings = settings
    app.state.store = store
    app.state.storage_service = storage_service
    app.state.search_service = search_service
    app.state.document_service = document_service
    app.state.chat_service = chat_service
    app.state.orchestrator = orchestrator

    await document_service.ensure_storage()
    await search_service.ensure_index_exists()
    stale_ids = await document_service.recover_stale_jobs()
    await orchestrator.recover(stale_ids)
    yield


app = FastAPI(title="PDF Multi-Agent RAG API", version="0.1.0", lifespan=lifespan)
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware, settings=settings)


@app.middleware("http")
async def attach_request_context(request: Request, call_next):
    correlation_id = str(uuid4())
    request.state.correlation_id = correlation_id
    logger = structlog.get_logger("request")
    logger.info("request_started", correlation_id=correlation_id, method=request.method, path=request.url.path)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    logger.info(
        "request_completed",
        correlation_id=correlation_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )
    return response


app.include_router(health.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        payload = exc.detail
    else:
        payload = {"error": "request_error", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=payload)
