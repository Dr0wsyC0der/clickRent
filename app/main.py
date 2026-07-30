from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
from app.api.v1.routes.users.users import router as users_router
from app.api.v1.routes.auth.auth import router as auth_router
from app.api.handlers.register import register_exception_handlers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Бэкэнд запущен!")

    yield

    logger.info("Бэкэнд остановлен!")


app = FastAPI(
    title="ClickRent API",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Добро пожаловать в API сервиса clickRent!"}

@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "service": "ClickRent API",
    }


if __name__ == "__main__":
    main()