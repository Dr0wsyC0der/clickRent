import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


async def integrity_error_handler(request: Request, exc: IntegrityError):
    # Срабатывает, когда параллельный запрос успел записать конфликтующие данные раньше
    logger.warning("Нарушение ограничения БД: %s %s: %s", request.method, request.url.path, exc.orig)
    return JSONResponse(
        status_code=409,
        content={"detail": "Конфликт данных: запись нарушает ограничения целостности."},
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Необработанная ошибка: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера."},
    )
