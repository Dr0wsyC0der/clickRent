import json
from fastapi import APIRouter, Depends, Query, Response, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from app.models.users import User
from app.repositories.user import UserRepository
from app.services.chat import ChatService
from app.schemas.chat import ChatCreate, ChatResponse, ChatListParams, ChatListResponse
from app.schemas.message import MessageCreate, MessageResponse, MessageListParams, MessageListResponse
from app.api.dependencies.chat import get_chat_service
from app.api.dependencies.repositories import get_user_repository
from app.api.dependencies.auth import get_current_user, get_optional_current_user
from app.exceptions.chat import ChatNotFoundException, ChatAccessDeniedException
from app.websocket.codes import WS_UNAUTHORIZED, WS_FORBIDDEN, WS_NOT_FOUND
from app.websocket.manager import chat_manager

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    response: Response,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    chat, created = await chat_service.get_or_create_direct_chat(
        user_id=current_user.id,
        participant_id=chat_data.participant_id,
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return chat

@router.get("/", response_model=ChatListResponse, status_code=status.HTTP_200_OK)
async def get_my_chats(
    params: ChatListParams = Depends(),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    chats, total = await chat_service.get_user_chats(
        user_id=current_user.id,
        page=params.page,
        size=params.size,
    )
    pages = (total + params.size - 1) // params.size
    return ChatListResponse(
        chats=chats,
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )

@router.get("/{chat_id}", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    return await chat_service.get_chat(chat_id=chat_id, user_id=current_user.id)

@router.get("/{chat_id}/messages", response_model=MessageListResponse, status_code=status.HTTP_200_OK)
async def get_chat_messages(
    chat_id: int,
    params: MessageListParams = Depends(),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    messages, total = await chat_service.get_messages(
        chat_id=chat_id,
        user_id=current_user.id,
        page=params.page,
        size=params.size,
    )
    pages = (total + params.size - 1) // params.size
    return MessageListResponse(
        messages=messages,
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )

@router.post("/{chat_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    chat_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    return await chat_service.send_message(
        chat_id=chat_id,
        sender=current_user,
        content=message_data.content,
    )

@router.websocket("/{chat_id}/ws")
async def chat_websocket(
    websocket: WebSocket,
    chat_id: int,
    token: str | None = Query(None, description="Access-токен (браузер не может передать заголовок в WebSocket)"),
    user_repository: UserRepository = Depends(get_user_repository),
    chat_service: ChatService = Depends(get_chat_service),
):
    await websocket.accept()

    current_user = await get_optional_current_user(token=token, user_repository=user_repository)
    if current_user is None:
        await websocket.close(code=WS_UNAUTHORIZED, reason="Требуется авторизация")
        return

    try:
        await chat_service.authorize_connection(chat_id=chat_id, user_id=current_user.id)
    except ChatNotFoundException as exc:
        await websocket.close(code=WS_NOT_FOUND, reason=str(exc))
        return
    except ChatAccessDeniedException as exc:
        await websocket.close(code=WS_FORBIDDEN, reason=str(exc))
        return

    chat_manager.connect(chat_id, websocket, current_user.id)
    try:
        await websocket.send_json({"type": "connected", "chat_id": chat_id})
        while True:
            raw_message = await websocket.receive_text()
            try:
                message_data = MessageCreate.model_validate(json.loads(raw_message))
            except (json.JSONDecodeError, ValidationError):
                await websocket.send_json({
                    "type": "error",
                    "detail": "Ожидается JSON вида {\"content\": \"текст\"} длиной от 1 до 2000 символов.",
                })
                continue

            await chat_service.send_message(
                chat_id=chat_id,
                sender=current_user,
                content=message_data.content,
            )
    except WebSocketDisconnect:
        pass
    finally:
        chat_manager.disconnect(chat_id, websocket)
