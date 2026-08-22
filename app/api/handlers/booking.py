from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.booking import (
    PropertyNotFoundException,
    BookingConflictException,
    InvalidBookingDatesException,
    BookingNotFoundException,
    BookingAccessDeniedException,
    BookingStatusException,
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

async def booking_not_found_handler(request: Request, exc: BookingNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Бронирование с указанным идентификатором не найдено"},
    )

async def booking_access_denied_handler(request: Request, exc: BookingAccessDeniedException):
    return JSONResponse(
        status_code=403,
        content={"detail": "У вас нет доступа к этому бронированию"},
    )

async def booking_status_exception_handler(request: Request, exc: BookingStatusException):
    return JSONResponse(
        status_code=409,
        content={"detail": "Менять статус бронирования на отмененный невозможно, так как оно уже завершено или отменено"},
    )