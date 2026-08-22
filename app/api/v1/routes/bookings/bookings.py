from fastapi import APIRouter, Depends, status
from app.models.users import User
from app.services.booking import BookingService
from app.schemas.booking import CreateBooking, BookingResponse
from app.api.dependencies.booking import get_booking_service
from app.api.dependencies.auth import get_current_user

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: CreateBooking,
    current_user: User = Depends(get_current_user),
    booking_service: BookingService = Depends(get_booking_service)
):
    new_booking = await booking_service.create_booking(
        user_id=current_user.id,
        property_id=booking_data.property_id,
        check_in=booking_data.check_in,
        check_out=booking_data.check_out
    )
    return new_booking

@router.get("/my", response_model=list[BookingResponse], status_code=status.HTTP_200_OK)
async def get_user_bookings(
    current_user: User = Depends(get_current_user),
    booking_service: BookingService = Depends(get_booking_service)
):
    return await booking_service.get_user_bookings(current_user.id)

@router.get("/{booking_id}", response_model=BookingResponse, status_code=status.HTTP_200_OK)
async def get_booking_by_id(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    booking_service: BookingService = Depends(get_booking_service)
):
    return await booking_service.get_booking_by_id(booking_id, current_user.id)

@router.post("/{booking_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    booking_service: BookingService = Depends(get_booking_service)
):
    await booking_service.cancel_booking(booking_id, current_user.id)