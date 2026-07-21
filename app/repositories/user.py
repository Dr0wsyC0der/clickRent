from app.models.users import User as UserModel
from app.repositories.base import BaseRepository
from sqlalchemy import select


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: int) -> UserModel | None:
        result = await self.session.scalars(select(UserModel).where(UserModel.id == user_id))
        return result.first()

    async def get_by_email(self, user_email: str) -> UserModel | None:
        result = await self.session.scalars(select(UserModel).where(UserModel.email == user_email))
        return result.first()
    
    async def create(self, user: UserModel) -> UserModel:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update(self, user: UserModel) -> UserModel:
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def delete(self, user: UserModel):
        await self.session.delete(user)
        await self.session.commit()