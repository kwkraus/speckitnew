from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse

from app.auth.dependencies import CurrentUser, get_current_user


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_documents(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    file: list[UploadFile] = File(...),
) -> Any:
    document_service = request.app.state.document_service
    orchestrator = request.app.state.orchestrator
    settings = request.app.state.settings

    responses: list[dict[str, Any]] = []
    for upload in file:
        if not upload.filename or not upload.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_file", "message": "File must be a PDF and not exceed 50 MB."},
            )

        data = await upload.read()
        if len(data) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_file", "message": "File must be a PDF and not exceed 50 MB."},
            )

        created, duplicate = await document_service.create_document(user, upload.filename, len(data), data)
        if duplicate is not None and len(file) == 1:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": "duplicate_document",
                    "message": "A document with identical content already exists.",
                    "existing_document": duplicate,
                },
            )
        if duplicate is not None:
            responses.append({"filename": upload.filename, "status": "duplicate", "existing_document": duplicate})
            continue

        await orchestrator.submit(created["id"])
        responses.append(
            {
                "id": created["id"],
                "filename": created["filename"],
                "status": created["status"],
                "file_size": created["file_size"],
                "created_at": created["created_at"].isoformat(),
            }
        )

    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=responses[0] if len(responses) == 1 else responses)


@router.get("")
async def list_documents(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> dict[str, Any]:
    result = await request.app.state.document_service.list_documents(user.user_id, page, page_size, status)
    return result.model_dump(mode="json")


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    document = await request.app.state.document_service.get_document(user.user_id, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Document not found."})
    return document.model_dump(mode="json")


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    status_payload = await request.app.state.document_service.get_status(user.user_id, document_id)
    if status_payload is None:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Document not found."})
    return status_payload.model_dump(mode="json")


@router.post("/{document_id}/replace")
async def replace_document(
    document_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    file: UploadFile = File(...),
) -> JSONResponse:
    data = await file.read()
    created, duplicate = await request.app.state.document_service.replace_document(
        user, document_id, file.filename or "replacement.pdf", len(data), data
    )
    if duplicate is not None:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "duplicate_document",
                "message": "A document with identical content already exists.",
                "existing_document": duplicate,
            },
        )
    await request.app.state.orchestrator.submit(created["id"])
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "id": created["id"],
            "filename": created["filename"],
            "status": created["status"],
            "replaced_document_id": document_id,
            "created_at": created["created_at"].isoformat(),
        },
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> JSONResponse:
    deleted = await request.app.state.document_service.delete_document(user.user_id, document_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Document not found."})
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"id": document_id, "status": "deleting", "message": "Document and index entries are being removed."},
    )

