from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationResponse
from app.models.notifications import Notification as NotificationModel
from app.exceptions.notification import NotificationNotFoundException
from app.db.enums import NotificationType


class NotificationService:
    def __init__(self,notification_repository: NotificationRepository,):
        self.notification_repository = notification_repository


    async def create_notification(self,user_id: int,notification_type: NotificationType,title: str,message: str,) -> NotificationModel:
        notification = NotificationModel(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
        )
        try:
            notification = await self.notification_repository.create(notification)
            await self.notification_repository.session.commit()
        except Exception:
            await self.notification_repository.session.rollback()
            raise

        return notification

    async def get_notification_by_id(
        self,
        notification_id: int,
        user_id: int,
    ) -> NotificationModel:
        notification = await self.notification_repository.get_by_id(
            notification_id=notification_id,
            user_id=user_id,
        )

        if not notification:
            raise NotificationNotFoundException(
                "Уведомление не найдено"
            )

        return notification

    async def get_user_notifications(
        self,
        user_id: int,
        page: int,
        size: int,
    ) -> tuple[list[NotificationModel], int]:
        notifications, total = (
            await self.notification_repository.get_user_notifications(
                user_id=user_id,
                page=page,
                size=size,
            )
        )

        return notifications, total

    async def mark_as_read(
        self,
        notification_id: int,
        user_id: int,
    ) -> NotificationModel:
        notification = await self.get_notification_by_id(
            notification_id=notification_id,
            user_id=user_id,
        )

        if not notification.is_read:
            try:
                notification = await self.notification_repository.mark_as_read(
                    notification
                )
                await self.notification_repository.session.commit()
            except Exception:
                await self.notification_repository.session.rollback()
                raise

        return notification

    async def mark_all_as_read(self, user_id: int) -> None:
        try:
            await self.notification_repository.mark_all_as_read(user_id)
            await self.notification_repository.session.commit()
        except Exception:
            await self.notification_repository.session.rollback()
            raise

    async def delete_notification(
        self,
        notification_id: int,
        user_id: int,
    ) -> None:
        notification = await self.get_notification_by_id(
            notification_id=notification_id,
            user_id=user_id,
        )

        try:
            await self.notification_repository.delete(notification)
            await self.notification_repository.session.commit()
        except Exception:
            await self.notification_repository.session.rollback()
            raise