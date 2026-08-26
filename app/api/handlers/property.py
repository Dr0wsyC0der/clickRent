from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.property import (
    PropertyAlreadyExistsException,
    PropertyNotFoundException,
    PropertyAccessDeniedException
)

async def property_already_exists_handler(request: Request, exc: PropertyAlreadyExistsException):
    return JSONResponse(
        status_code=409,
        content={"detail": "Такая недвижимость уже существует"},
    )

async def property_not_found_handler(request: Request, exc: PropertyNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Недвижимость не найдена"},
    )

async def property_access_denied_handler(request: Request, exc: PropertyAccessDeniedException):
    return JSONResponse(
        status_code=403,
        content={"detail": "Доступ к недвижимости запрещен"},
    )