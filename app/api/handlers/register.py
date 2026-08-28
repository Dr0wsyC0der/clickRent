from fastapi import FastAPI

from app.api.handlers.auth import (
    email_exists_handler,
    username_exists_handler,
    invalid_credentials_handler,
    invalid_refresh_token_handler,
    refresh_token_expired_handler,
    refresh_token_revoked_handler,
    admin_access_denied_handler
)

from app.exceptions.auth import (
    EmailAlreadyExistsException,
    UsernameAlreadyExistsException,
    InvalidCredentialsException,
    InvalidRefreshTokenException,
    RefreshTokenExpiredException,
    RefreshTokenRevokedException,
    AdminAccessDeniedException,
)

from app.api.handlers.booking import (
    property_not_found_handler,
    booking_conflict_handler,
    invalid_booking_dates_handler,
    booking_not_found_handler,
    booking_access_denied_handler,
    booking_status_exception_handler,

)

from app.exceptions.booking import (
    PropertyNotFoundException,
    BookingConflictException,
    InvalidBookingDatesException,
    BookingNotFoundException,
    BookingAccessDeniedException,
    BookingStatusException,
)

from app.api.handlers.property import (
    property_already_exists_handler,
    property_not_found_handler,
    property_access_denied_handler,
)

from app.exceptions.property import (
    PropertyAlreadyExistsException,
    PropertyNotFoundException,
    PropertyAccessDeniedException,
)

from app.api.handlers.review import (
    review_not_found_handler,
    review_access_denied_handler,
    review_already_exists_handler,
)

from app.exceptions.review import (
    ReviewNotFoundException,
    ReviewAccessDeniedException,
    ReviewAlreadyExistsException,
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
        AdminAccessDeniedException,
        admin_access_denied_handler,
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

    app.add_exception_handler(
        BookingNotFoundException,
        booking_not_found_handler,
    )

    app.add_exception_handler(
        BookingAccessDeniedException,
        booking_access_denied_handler,
    )

    app.add_exception_handler(
        BookingStatusException,
        booking_status_exception_handler,
    )

    app.add_exception_handler(
        PropertyAlreadyExistsException,
        property_already_exists_handler,
    )

    app.add_exception_handler(
        PropertyNotFoundException,
        property_not_found_handler,
    )

    app.add_exception_handler(
        PropertyAccessDeniedException,
        property_access_denied_handler,
    )

    app.add_exception_handler(
        ReviewAccessDeniedException,
        review_access_denied_handler,
    )

    app.add_exception_handler(
        ReviewAlreadyExistsException,
        review_already_exists_handler,
    )

    app.add_exception_handler(
        ReviewNotFoundException,
        review_not_found_handler,
    )
    