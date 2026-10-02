import asyncio
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
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
from app.api.handlers.register import register_exception_handlers
from app.core.config import settings
from app.db.database import async_session_maker
from app.tasks.booking import run_booking_maintenance


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Бэкэнд запущен!")

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

    logger.info("Бэкэнд остановлен!")


app = FastAPI(
    title="ClickRent API",
    lifespan=lifespan,
)

app.mount("/media", StaticFiles(directory="media"), name="media")

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


@app.get("/")
async def root():
    return {"message": "Добро пожаловать в API сервиса clickRent!"}

@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "service": "ClickRent API",
    }

