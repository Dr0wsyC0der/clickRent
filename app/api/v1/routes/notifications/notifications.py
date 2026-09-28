from math import ceil
from fastapi import APIRouter, Depends, status
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.notification import get_notification_service
from app.models.users import User
from app.schemas.notification import (
    NotificationListParams,
    NotificationListResponse,
    NotificationResponse,
)
from app.services.notification import NotificationService

router = APIRouter(prefix="/notifications",tags=["notifications"],)

@router.get("/",response_model=NotificationListResponse,status_code=status.HTTP_200_OK)
async def get_notifications(
    params: NotificationListParams = Depends(),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    notifications, total = await notification_service.get_user_notifications(
        user_id=current_user.id,
        page=params.page,
        size=params.size,
    )

    pages = ceil(total / params.size) if total else 0

    return NotificationListResponse(
        notifications=notifications,
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


@router.get("/{notification_id}",response_model=NotificationResponse,status_code=status.HTTP_200_OK)
async def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    return await notification_service.get_notification_by_id(
        notification_id=notification_id,
        user_id=current_user.id,
    )


@router.patch("/{notification_id}/read",response_model=NotificationResponse,status_code=status.HTTP_200_OK)
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    return await notification_service.mark_as_read(
        notification_id=notification_id,
        user_id=current_user.id,
    )


@router.patch("/read-all",status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    await notification_service.mark_all_as_read(
        user_id=current_user.id,
    )


@router.delete("/{notification_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    await notification_service.delete_notification(
        notification_id=notification_id,
        user_id=current_user.id,
    )