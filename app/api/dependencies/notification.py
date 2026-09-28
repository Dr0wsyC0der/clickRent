from fastapi import Depends
from app.services.notification import NotificationService
from app.repositories.notification import NotificationRepository
from app.api.dependencies.repositories import get_notification_repository

async def get_notification_service(
        notification_repository: NotificationRepository = Depends(get_notification_repository)
        ) -> NotificationService:
    return NotificationService(notification_repository=notification_repository)