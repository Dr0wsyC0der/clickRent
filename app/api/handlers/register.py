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

from app.api.handlers.booking import (
    property_not_found_handler,
    booking_conflict_handler,
    invalid_booking_dates_handler,
)

from app.exceptions.booking import (
    PropertyNotFoundException,
    BookingConflictException,
    InvalidBookingDatesException,
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

    app.add_exception_handler(
        BookingConflictException,
        booking_conflict_handler,
    )

    app.add_exception_handler(
        InvalidBookingDatesException,
        invalid_booking_dates_handler,
    )

    app.add_exception_handler(
        PropertyNotFoundException,
        property_not_found_handler,
    )