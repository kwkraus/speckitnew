from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.auth.dependencies import CurrentUser, get_current_user
from app.models.conversation import ConversationCreate, ConversationListResponse, MessageRequest


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    conversation = await request.app.state.chat_service.create_conversation(user, payload.title)
    return conversation.model_dump(mode="json")


@router.get("/conversations")
async def list_conversations(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    page: int = 1,
    page_size: int = 20,
) -> dict:
    items = await request.app.state.chat_service.list_conversations(user, page, page_size)
    response = ConversationListResponse(
        conversations=items,
        total=len([item for item in request.app.state.store.conversations.values() if item["user_id"] == user.user_id]),
        page=page,
        page_size=page_size,
    )
    return response.model_dump(mode="json")


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    conversation = await request.app.state.chat_service.get_conversation(user, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Conversation not found."})
    return conversation.model_dump(mode="json")


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    payload: MessageRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    if not payload.content.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_message", "message": "Message content cannot be empty."},
        )
    if not request.app.state.document_service.has_completed_documents(user.user_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "no_documents",
                "message": "No documents have been indexed yet. Upload and process at least one document before chatting.",
            },
        )

    message_response = await request.app.state.chat_service.send_message(user, conversation_id, payload.content)
    if message_response is None:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Conversation not found."})
    return message_response.model_dump(mode="json")


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> Response:
    deleted = await request.app.state.chat_service.delete_conversation(user, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Conversation not found."})
    return Response(status_code=status.HTTP_204_NO_CONTENT)

