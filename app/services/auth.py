import re
import uuid
from datetime import datetime, timezone
from app.repositories.user import UserRepository 
from app.repositories.refresh_token import RefreshTokenRepository
from app.models.users import User as UserModel
from app.models.refresh_tokens import RefreshToken as RefreshTokenModel
from app.security.hashing import hash_password, verify_password, hash_refresh_token
from app.exceptions.auth import EmailAlreadyExistsException, UsernameAlreadyExistsException, InvalidCredentialsException, InvalidRefreshTokenException, RefreshTokenRevokedException, RefreshTokenExpiredException
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
)
from app.security.jwt import create_access_token, create_refresh_token, decode_token


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
    ):
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository

    async def register(self, data: RegisterRequest) -> UserModel | None :
        result_email = await self.user_repository.get_by_email(data.email)
        if result_email:
            raise EmailAlreadyExistsException()
        
        result_username = await self.user_repository.get_by_username(data.username)
        if result_username:
            raise UsernameAlreadyExistsException()
        
        password_hash = hash_password(password=data.password)

        new_user = UserModel(
            email = data.email,
            username = data.username,
            password_hash = password_hash,
        )

        new_user = await self.user_repository.create(new_user)

        return new_user

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self._find_user(data.login)
        if not user:
            raise InvalidCredentialsException()
        
        password_is_valid = verify_password(
            data.password,
            user.password_hash,
        )
        if not password_is_valid:
            raise InvalidCredentialsException()
        
        return await self._create_token_pair(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        refresh, payload = await self._get_refresh_token(refresh_token)

        user_id = payload.get("sub")
        if user_id is None:
            raise InvalidRefreshTokenException()

        user = await self.user_repository.get_by_id(int(user_id))
        if not user:
            raise InvalidRefreshTokenException()

        await self.refresh_token_repository.revoke(refresh)

        return await self._create_token_pair(user)
    

    async def logout(self, refresh_token: str) -> None:
        refresh, _ = await self._get_refresh_token(refresh_token)

        await self.refresh_token_repository.revoke(refresh)

    async def _find_user(self, login: str) -> UserModel | None:
        login = login.strip()
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        phone_regex = r"^\+?[1-9]\d{1,14}$"
        if re.match(email_regex, login):
            result = await self.user_repository.get_by_email(login)
        elif re.match(phone_regex, login):
            result = await self.user_repository.get_by_phone(login)
        else:
            result = await self.user_repository.get_by_username(login)

        return result if result else None

    async def _create_token_pair(self, user: UserModel) -> TokenResponse:
        payload = {
            "sub": str(user.id),
            "jti": str(uuid.uuid4()),
        }

        access_token, _ = create_access_token(payload)
        refresh_token, expires_at = create_refresh_token(payload)

        refresh = RefreshTokenModel(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=expires_at,
        )

        await self.refresh_token_repository.create(refresh)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def _get_refresh_token(self, refresh_token: str) -> tuple[RefreshTokenModel, dict]:
        payload = decode_token(token=refresh_token)
        if payload.get("type") != "refresh":
            raise InvalidRefreshTokenException()
        
        hashed_token = hash_refresh_token(refresh_token)
        result = await self.refresh_token_repository.get_by_token_hash(hashed_token)
        if not result:
            raise InvalidRefreshTokenException()
        if result.is_revoked:
            raise RefreshTokenRevokedException()
        if result.expires_at < datetime.now(timezone.utc):
            raise RefreshTokenExpiredException()
        
        return result, payload