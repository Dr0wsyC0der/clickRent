from fastapi import FastAPI

from app.api.handlers.auth import (
    email_exists_handler,
    username_exists_handler,
    invalid_credentials_handler,
    invalid_refresh_token_handler,
    refresh_token_expired_handler,
    refresh_token_revoked_handler,
)

from app.exceptions.auth import (
    EmailAlreadyExistsException,
    UsernameAlreadyExistsException,
    InvalidCredentialsException,
    InvalidRefreshTokenException,
    RefreshTokenExpiredException,
    RefreshTokenRevokedException,
)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        EmailAlreadyExistsException,
        email_exists_handler,
    )

    app.add_exception_handler(
        UsernameAlreadyExistsException,
        username_exists_handler,
    )

    app.add_exception_handler(
        InvalidCredentialsException,
        invalid_credentials_handler,
    )

    app.add_exception_handler(
        InvalidRefreshTokenException,
        invalid_refresh_token_handler,
    )

    app.add_exception_handler(
        RefreshTokenExpiredException,
        refresh_token_expired_handler,
    )

    app.add_exception_handler(
        RefreshTokenRevokedException,
        refresh_token_revoked_handler,
    )