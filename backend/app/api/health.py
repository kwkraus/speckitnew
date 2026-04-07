from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse


router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(request: Request) -> JSONResponse:
    store = request.app.state.store
    services = {
        "cosmos_db": "connected" if store.cosmos_ready else "error",
        "ai_search": "connected" if store.search_index_ready else "error",
        "blob_storage": "connected",
        "openai": "connected",
        "document_intelligence": "connected",
    }
    degraded = any(state != "connected" for state in services.values())
    payload = {"status": "degraded" if degraded else "healthy", "services": services}
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE if degraded else 200, content=payload)

