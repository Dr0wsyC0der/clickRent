from fastapi import Depends

from app.services.property_signal import PropertySignalService
from app.repositories.property import PropertyRepository
from app.repositories.property_view import PropertyViewRepository
from app.repositories.favorite import FavoriteRepository
from app.repositories.booking import BookingRepository
from app.api.dependencies.repositories import (
    get_property_repository,
    get_property_view_repository,
    get_favorite_repository,
    get_booking_repository,
)
from app.websocket.manager import property_viewers_manager


async def get_property_signal_service(
    property_repository: PropertyRepository = Depends(get_property_repository),
    property_view_repository: PropertyViewRepository = Depends(get_property_view_repository),
    favorite_repository: FavoriteRepository = Depends(get_favorite_repository),
    booking_repository: BookingRepository = Depends(get_booking_repository),
) -> PropertySignalService:
    return PropertySignalService(
        property_repository=property_repository,
        property_view_repository=property_view_repository,
        favorite_repository=favorite_repository,
        booking_repository=booking_repository,
        viewers_manager=property_viewers_manager,
    )
