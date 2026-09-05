from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.favorite import (
    AlreadyAddedToFavoritesException,
    FavoriteNotFoundException
)

async def already_added_to_favorites_handler(request: Request, exc: AlreadyAddedToFavoritesException):
    return JSONResponse(
        status_code=409,
        content={"detail": "Недвижимость уже добавлена в избранное"},
    )

async def favorite_not_found_handler(request: Request, exc: FavoriteNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Недвижимость не найдена в избранном"},
    )   

