from fastapi.responses import JSONResponse
from fastapi import Request

from app.exceptions.amenity import (
    AmenityNotFoundException,
    AmenityAlreadyAddedException,
    AmenityNotAddedException,
)

async def amenity_not_found_handler(request: Request, exc: AmenityNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Удобства не найдены"},
    )

async def amenity_already_added_handler(request: Request, exc: AmenityAlreadyAddedException):
    return JSONResponse(
        status_code=409,
        content={"detail": "Удобство уже добавлено к этой недвижимости"},
    )

async def amenity_not_added_handler(request: Request, exc: AmenityAlreadyAddedException):
    return JSONResponse(
        status_code=409,
        content={"detail": "Такого удобства нет у этой недвижиомсти"},
    )