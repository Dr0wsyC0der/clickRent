from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

async_engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
)

async_session_maker = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)
