from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.booking import (
    PropertyNotFoundException,
    BookingConflictException,
    InvalidBookingDatesException,
)

async def property_not_found_handler(request: Request, exc: PropertyNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Объект недвижимости не найден"},
    )

async def booking_conflict_handler(request: Request, exc: BookingConflictException):
    return JSONResponse(
        status_code=409,
        content={"detail": "Конфликт бронирования: выбранные даты уже заняты"},
    )

async def invalid_booking_dates_handler(request: Request, exc: InvalidBookingDatesException):
    return JSONResponse(
        status_code=400,
        content={"detail": "Неверные даты бронирования"},
    )