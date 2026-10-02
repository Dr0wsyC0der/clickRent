from fastapi import Depends
from app.services.chat import ChatService
from app.services.notification import NotificationService
from app.repositories.chat import ChatRepository
from app.repositories.user import UserRepository
from app.api.dependencies.notification import get_notification_service
from app.api.dependencies.repositories import get_chat_repository, get_user_repository
from app.websocket.manager import chat_manager

async def get_chat_service(
        chat_repository: ChatRepository = Depends(get_chat_repository),
        user_repository: UserRepository = Depends(get_user_repository),
        notification_service: NotificationService = Depends(get_notification_service),
        ) -> ChatService:
    return ChatService(
        chat_repository=chat_repository,
        user_repository=user_repository,
        notification_service=notification_service,
        connection_manager=chat_manager,
    )
