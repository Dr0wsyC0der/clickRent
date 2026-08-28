from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.review import (
    ReviewNotFoundException,
    ReviewAlreadyExistsException,
    ReviewAccessDeniedException
)

async def review_not_found_handler(request: Request, exc: ReviewNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Отзыв не найден"},
    )   

async def review_access_denied_handler(request: Request, exc: ReviewAccessDeniedException):
    return JSONResponse(
        status_code=403,
        content={"detail": "Доступ к отзыву запрещен"},
    )   

async def review_already_exists_handler(request: Request, exc: ReviewAlreadyExistsException):
    return JSONResponse(
        status_code=409,
        content={"detail": "Отзыв уже существует"},
    )   