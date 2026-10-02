from app.repositories.chat import ChatRepository
from app.repositories.user import UserRepository
from app.services.notification import NotificationService
from app.models.chats import Chat as ChatModel
from app.models.messages import Message as MessageModel
from app.models.users import User as UserModel
from app.schemas.chat import ChatResponse
from app.schemas.message import MessageResponse
from app.websocket.manager import ConnectionManager
from app.exceptions.chat import (
    ChatNotFoundException,
    ChatAccessDeniedException,
    ChatParticipantNotFoundException,
    InvalidChatParticipantException,
)
from app.db.enums import NotificationType

MESSAGE_PREVIEW_LENGTH = 100


class ChatService:
    def __init__(
        self,
        chat_repository: ChatRepository,
        user_repository: UserRepository,
        notification_service: NotificationService,
        connection_manager: ConnectionManager,
    ):
        self.chat_repository = chat_repository
        self.user_repository = user_repository
        self.notification_service = notification_service
        self.connection_manager = connection_manager

    async def get_or_create_direct_chat(self, user_id: int, participant_id: int) -> tuple[ChatResponse, bool]:
        if participant_id == user_id:
            raise InvalidChatParticipantException("Нельзя создать чат с самим собой.")
        participant = await self.user_repository.get_by_id(participant_id)
        if participant is None:
            raise ChatParticipantNotFoundException("Пользователь, с которым вы хотите начать чат, не найден.")

        try:
            await self.chat_repository.lock_direct_chat(user_id, participant_id)
            chat = await self.chat_repository.get_direct_chat(user_id, participant_id)
            created = chat is None
            if created:
                chat = await self.chat_repository.create([user_id, participant_id])
            await self.chat_repository.commit()
        except Exception:
            await self.chat_repository.rollback()
            raise

        return (await self._build_chat_responses([chat]))[0], created

    async def get_chat(self, chat_id: int, user_id: int) -> ChatResponse:
        chat = await self._get_chat_for_participant(chat_id, user_id)
        return (await self._build_chat_responses([chat]))[0]

    async def authorize_connection(self, chat_id: int, user_id: int) -> None:
        await self._get_chat_for_participant(chat_id, user_id)
        # Завершаем читающую транзакцию, чтобы долгоживущее WebSocket-подключение не держало ее открытой
        await self.chat_repository.commit()

    async def get_user_chats(self, user_id: int, page: int, size: int) -> tuple[list[ChatResponse], int]:
        chats, total = await self.chat_repository.get_user_chats(user_id, page, size)
        return await self._build_chat_responses(chats), total

    async def get_messages(self, chat_id: int, user_id: int, page: int, size: int) -> tuple[list[MessageModel], int]:
        await self._get_chat_for_participant(chat_id, user_id)
        return await self.chat_repository.get_messages(chat_id, page, size)

    async def send_message(self, chat_id: int, sender: UserModel, content: str) -> MessageModel:
        await self._get_chat_for_participant(chat_id, sender.id)

        try:
            message = await self.chat_repository.add_message(
                MessageModel(chat_id=chat_id, sender_id=sender.id, content=content)
            )
            participant_ids = (await self.chat_repository.get_participant_ids([chat_id]))[chat_id]
            await self.chat_repository.commit()
        except Exception:
            await self.chat_repository.rollback()
            raise

        # Уведомление получают только те участники, у кого сейчас не открыт этот чат
        preview = content if len(content) <= MESSAGE_PREVIEW_LENGTH else content[:MESSAGE_PREVIEW_LENGTH] + "…"
        for participant_id in participant_ids:
            if participant_id == sender.id or self.connection_manager.is_user_connected(chat_id, participant_id):
                continue
            await self.notification_service.create_notification(
                user_id=participant_id,
                notification_type=NotificationType.NEW_MESSAGE,
                title="Новое сообщение",
                message=f"{sender.username}: {preview}",
            )

        await self.connection_manager.broadcast(chat_id, {
            "type": "message",
            "message": MessageResponse.model_validate(message).model_dump(mode="json"),
        })

        return message

    async def _get_chat_for_participant(self, chat_id: int, user_id: int) -> ChatModel:
        chat = await self.chat_repository.get_by_id(chat_id)
        if chat is None:
            raise ChatNotFoundException("Чат не найден.")
        if not await self.chat_repository.is_participant(chat_id, user_id):
            raise ChatAccessDeniedException("Вы не являетесь участником этого чата.")
        return chat

    async def _build_chat_responses(self, chats: list[ChatModel]) -> list[ChatResponse]:
        chat_ids = [chat.id for chat in chats]
        participants = await self.chat_repository.get_participant_ids(chat_ids)
        last_messages = await self.chat_repository.get_last_messages(chat_ids)
        return [
            ChatResponse(
                id=chat.id,
                participant_ids=participants[chat.id],
                last_message=(
                    MessageResponse.model_validate(last_messages[chat.id])
                    if chat.id in last_messages else None
                ),
                created_at=chat.created_at,
                updated_at=chat.updated_at,
            )
            for chat in chats
        ]
