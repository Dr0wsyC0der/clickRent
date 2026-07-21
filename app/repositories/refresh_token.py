from app.repositories.base import BaseRepository
from app.models.refresh_tokens import RefreshToken as RefreshTokenModel
from sqlalchemy import select, update


class RefreshTokenRepository(BaseRepository):
    async def create(self, refresh_token: RefreshTokenModel) -> RefreshTokenModel:
        self.session.add(refresh_token)
        await self.session.commit()
        await self.session.refresh(refresh_token)
        return refresh_token

    async def get_by_token_hash(self, refresh_token_hash: str) -> RefreshTokenModel | None:
        result = await self.session.scalars(select(RefreshTokenModel).where(RefreshTokenModel.token_hash == refresh_token_hash))
        return result.first()

    async def revoke(self, refresh_token: RefreshTokenModel) -> RefreshTokenModel | None:
        refresh_token.is_revoked = True
        await self.session.commit()
        return refresh_token

    async def revoke_all(self, user_id: int) -> None:
        stmt = update(RefreshTokenModel).where(RefreshTokenModel.user_id == user_id).values(is_revoked = True)
        await self.session.execute(stmt)
        await self.session.commit()







