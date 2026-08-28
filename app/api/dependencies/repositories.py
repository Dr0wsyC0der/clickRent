from fastapi import Depends
from app.api.dependencies.db import get_session
from app.repositories.user import UserRepository
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.repositories.review import ReviewRepository
from app.repositories.refresh_token import RefreshTokenRepository
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session=session)

async def get_booking_repository(session: AsyncSession = Depends(get_session)) -> BookingRepository:
    return BookingRepository(session=session)

async def get_property_repository(session: AsyncSession = Depends(get_session)) -> PropertyRepository:
    return PropertyRepository(session=session)

async def get_refresh_token_repository(session: AsyncSession = Depends(get_session)) -> RefreshTokenRepository:
    return RefreshTokenRepository(session=session)

async def get_review_repository(session: AsyncSession = Depends(get_session)) -> ReviewRepository:
    return ReviewRepository(session=session)