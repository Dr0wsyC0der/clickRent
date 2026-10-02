import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import logging
from app.api.v1.routes.users.users import router as users_router
from app.api.v1.routes.auth.auth import router as auth_router
from app.api.v1.routes.bookings.bookings import router as booking_router
from app.api.v1.routes.properties.properties import router as property_router
from app.api.v1.routes.amenities.amenities import router as amenity_router
from app.api.v1.routes.reviews.review import router as review_router
from app.api.v1.routes.favorities.favorite import router as favorite_router
from app.api.v1.routes.property_images.property_images import router as property_images_router
from app.api.v1.routes.notifications.notifications import router as notification_router
from app.api.v1.routes.chats.chats import router as chat_router
from app.api.handlers.register import register_exception_handlers
from app.api.dependencies.db import get_session
from app.api.dependencies.redis import get_redis_client
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.redis import create_redis, set_redis
from app.db.database import async_session_maker
from app.middleware.request_logging import RequestLoggingMiddleware
from app.tasks.booking import run_booking_maintenance

MEDIA_DIR = Path("media")

setup_logging(settings.log_level)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Бэкэнд запущен!")

    redis = create_redis(settings.redis_url)
    set_redis(redis)

    maintenance_task = None
    if settings.environment != "testing":
        maintenance_task = asyncio.create_task(
            run_booking_maintenance(async_session_maker, settings.booking_tasks_interval_seconds)
        )

    yield

    if maintenance_task is not None:
        maintenance_task.cancel()
        with suppress(asyncio.CancelledError):
            await maintenance_task

    set_redis(None)
    await redis.aclose()

    logger.info("Бэкэнд остановлен!")


app = FastAPI(
    title="ClickRent API",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

# На чистом окружении папки media еще нет, а StaticFiles требует ее существования
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

register_exception_handlers(app)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(booking_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(property_router, prefix="/api/v1")
app.include_router(amenity_router, prefix="/api/v1")
app.include_router(review_router, prefix="/api/v1")
app.include_router(property_images_router, prefix="/api/v1")
app.include_router(favorite_router, prefix="/api/v1")
app.include_router(notification_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Добро пожаловать в API сервиса clickRent!"}

@app.get("/health", tags=["Health"])
async def health():
    """Liveness: процесс жив и отвечает."""
    return {
        "status": "ok",
        "service": "ClickRent API",
    }

@app.get("/health/ready", tags=["Health"])
async def readiness(
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis_client),
):
    """Readiness: приложение может обслуживать запросы, PostgreSQL и Redis доступны."""
    checks = {"database": "ok", "redis": "ok"}

    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Проверка готовности: база данных недоступна")
        checks["database"] = "unavailable"

    try:
        await redis.ping()
    except Exception:
        logger.exception("Проверка готовности: Redis недоступен")
        checks["redis"] = "unavailable"

    if "unavailable" in checks.values():
        return JSONResponse(status_code=503, content={"status": "unavailable", **checks})
    return {"status": "ok", **checks}
