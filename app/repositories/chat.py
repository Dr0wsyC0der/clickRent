from sqlalchemy import select, func, update

from app.models.chats import Chat as ChatModel
from app.models.chat_participants import ChatParticipant as ChatParticipantModel
from app.models.messages import Message as MessageModel
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository):
    async def get_by_id(self, chat_id: int) -> ChatModel | None:
        result = await self.session.scalars(
            select(ChatModel)
            .where(ChatModel.id == chat_id)
            .execution_options(populate_existing=True)
        )
        return result.first()

    async def lock_direct_chat(self, user_id: int, other_user_id: int) -> None:
        # Advisory-блокировка пары пользователей не дает создать два одинаковых чата параллельно
        first, second = sorted((user_id, other_user_id))
        await self.session.execute(select(func.pg_advisory_xact_lock(first, second)))

    async def get_direct_chat(self, user_id: int, other_user_id: int) -> ChatModel | None:
        user_chats = select(ChatParticipantModel.chat_id).where(ChatParticipantModel.user_id == user_id)
        other_user_chats = select(ChatParticipantModel.chat_id).where(ChatParticipantModel.user_id == other_user_id)
        participants_count = (
            select(func.count())
            .select_from(ChatParticipantModel)
            .where(ChatParticipantModel.chat_id == ChatModel.id)
            .scalar_subquery()
        )
        result = await self.session.scalars(
            select(ChatModel).where(
                ChatModel.id.in_(user_chats),
                ChatModel.id.in_(other_user_chats),
                participants_count == 2,
            )
        )
        return result.first()

    async def create(self, participant_ids: list[int]) -> ChatModel:
        chat = ChatModel()
        self.session.add(chat)
        await self.session.flush()
        self.session.add_all(
            ChatParticipantModel(chat_id=chat.id, user_id=user_id)
            for user_id in participant_ids
        )
        await self.session.flush()
        await self.session.refresh(chat)
        return chat

    async def is_participant(self, chat_id: int, user_id: int) -> bool:
        result = await self.session.scalar(
            select(func.count())
            .select_from(ChatParticipantModel)
            .where(
                ChatParticipantModel.chat_id == chat_id,
                ChatParticipantModel.user_id == user_id,
            )
        )
        return bool(result)

    async def get_participant_ids(self, chat_ids: list[int]) -> dict[int, list[int]]:
        participants: dict[int, list[int]] = {chat_id: [] for chat_id in chat_ids}
        if not chat_ids:
            return participants
        result = await self.session.execute(
            select(ChatParticipantModel.chat_id, ChatParticipantModel.user_id)
            .where(ChatParticipantModel.chat_id.in_(chat_ids))
            .order_by(ChatParticipantModel.user_id)
        )
        for chat_id, user_id in result.all():
            participants[chat_id].append(user_id)
        return participants

    async def get_user_chats(self, user_id: int, page: int, size: int) -> tuple[list[ChatModel], int]:
        user_chats = select(ChatParticipantModel.chat_id).where(ChatParticipantModel.user_id == user_id)
        total = await self.session.scalar(
            select(func.count()).select_from(ChatModel).where(ChatModel.id.in_(user_chats))
        )
        result = await self.session.scalars(
            select(ChatModel)
            .where(ChatModel.id.in_(user_chats))
            .order_by(ChatModel.updated_at.desc(), ChatModel.id.desc())
            .offset((page - 1) * size)
            .limit(size)
            .execution_options(populate_existing=True)
        )
        return result.all(), total

    async def get_last_messages(self, chat_ids: list[int]) -> dict[int, MessageModel]:
        if not chat_ids:
            return {}
        result = await self.session.scalars(
            select(MessageModel)
            .where(MessageModel.chat_id.in_(chat_ids))
            .distinct(MessageModel.chat_id)
            .order_by(MessageModel.chat_id, MessageModel.created_at.desc(), MessageModel.id.desc())
        )
        return {message.chat_id: message for message in result.all()}

    async def add_message(self, message: MessageModel) -> MessageModel:
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        # Поднимаем чат вверх списка
        await self.session.execute(
            update(ChatModel)
            .where(ChatModel.id == message.chat_id)
            .values(updated_at=func.now())
            .execution_options(synchronize_session=False)
        )
        return message

    async def get_messages(self, chat_id: int, page: int, size: int) -> tuple[list[MessageModel], int]:
        total = await self.session.scalar(
            select(func.count()).select_from(MessageModel).where(MessageModel.chat_id == chat_id)
        )
        result = await self.session.scalars(
            select(MessageModel)
            .where(MessageModel.chat_id == chat_id)
            .order_by(MessageModel.created_at.desc(), MessageModel.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return result.all(), total
