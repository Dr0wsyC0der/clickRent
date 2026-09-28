from sqlalchemy import select, update, func
from app.models.notifications import Notification as NotificationModel
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    async def create(self, notification: NotificationModel) -> NotificationModel:
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        return notification

    async def get_by_id(self,notification_id: int,user_id: int,) -> NotificationModel | None:
        result = await self.session.scalars(
            select(NotificationModel).where(
                NotificationModel.id == notification_id,
                NotificationModel.user_id == user_id,
            )
        )
        return result.first()

    async def get_user_notifications(self, user_id: int, page: int, size: int,) -> tuple[list[NotificationModel], int]:
        count_query = (
            select(func.count())
            .select_from(NotificationModel)
            .where(NotificationModel.user_id == user_id)
        )

        total = await self.session.scalar(count_query)

        result = await self.session.scalars(
            select(NotificationModel)
            .where(NotificationModel.user_id == user_id)
            .order_by(NotificationModel.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )

        return result.all(), total

    async def mark_as_read(self, notification: NotificationModel) -> NotificationModel:
        notification.is_read = True
        await self.session.flush()
        await self.session.refresh(notification)
        return notification

    async def mark_all_as_read(self, user_id: int) -> None:
        await self.session.execute(
            update(NotificationModel)
            .where(
                NotificationModel.user_id == user_id,
                NotificationModel.is_read.is_(False),
            )
            .values(is_read=True)
        )
        await self.session.flush()

    async def delete(self, notification: NotificationModel) -> None:
        await self.session.delete(notification)
        await self.session.flush()