# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

ClickRent is an async FastAPI backend for short-term property rentals: users, properties, bookings (with a TTL soft-lock), reviews, favorites, amenities, property images, notifications, view tracking, WebSocket chat, and live viewer counts. It uses SQLAlchemy 2.0 (async, asyncpg), Alembic, and PostgreSQL 17. User-facing strings (exception messages, notification texts, log lines) and commit messages are written in Russian. Keep that convention.

## Commands

Run all commands from the repo root. The app mounts `media/` relative to the CWD, and settings load from `./.env`.

```bash
# Postgres only (service db, postgres/postgres on localhost:5432; also creates clickrent_test on first init)
docker compose up -d db

# Full stack: db + app (Gunicorn/UvicornWorker, runs migrations on start) + nginx on HTTP_PORT
docker compose up -d --build

# Dev server
uvicorn app.main:app --reload

# Migrations (env.py takes the URL from settings.database_url, not alembic.ini)
alembic upgrade head
alembic revision --autogenerate -m "description"

# Tests
pytest app/tests
pytest app/tests/bookings/test_booking.py
pytest app/tests/bookings/test_booking.py::test_name

# Lint (config in pyproject.toml)
ruff check .
```

- `.env` needs `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and `REFRESH_TOKEN_EXPIRE_DAYS` (see `.env.example`, which also lists optional settings and docker compose variables). `.env.example` points at `localhost`; docker compose overrides `DATABASE_URL` for the `app` container to use host `db`. Settings ignore unknown env vars (`extra="ignore"`).
- Tests need a separate, existing database `clickrent_test`. The URL defaults to `localhost:5432` and can be overridden with `TEST_DATABASE_URL`. Each test creates all tables with `Base.metadata.create_all` and drops them afterward, so tests skip Alembic.
- `pyproject.toml` sets only `pythonpath` for pytest, so pytest-asyncio runs in strict mode. Mark async tests with `@pytest.mark.asyncio` or a module-level `pytestmark = pytest.mark.asyncio`, and async fixtures with `@pytest_asyncio.fixture`.
- `requirements.txt` holds runtime dependencies (installed into the Docker image); `requirements-dev.txt` adds pytest, httpx, httpx-ws, and ruff. Both are UTF-8.
- Ruff runs pyflakes and syntax checks only (`E9`, `F`, with `F401` ignored). There is no formatter. CI (`.github/workflows/ci.yml`) runs ruff, migrations on a clean DB (`alembic check`, full downgrade/upgrade), pytest, and a Docker build with a `/health/ready` probe.
- PostgreSQL enum types use member names (`'PENDING'`). Adding an enum value needs a manual migration with `ALTER TYPE ... ADD VALUE IF NOT EXISTS`; autogenerate and `alembic check` do not detect it.

## Architecture

A request flows through these layers, each in its own package and split per domain (booking, property, review, and so on):

1. **Routes**: `app/api/v1/routes/<domain>/<file>.py`. Each one is an `APIRouter` with its own prefix, and `app/main.py` includes it under `/api/v1`. A new router has to be included manually in `main.py`. Handlers stay thin: they resolve the current user and service through `Depends` and call one service method.
2. **Dependencies**: `app/api/dependencies/`. `db.get_session` yields one `AsyncSession` per request. `repositories.py` builds every repository from that session, and per-domain modules (`booking.py`, `property.py`, …) put services together from repositories and other services. For example, `BookingService` gets `NotificationService`, and both share the same session. `auth.py` provides `get_current_user`, `get_optional_current_user` (for anonymous access, such as view tracking), `check_admin`, and `check_host`.
3. **Services**: `app/services/`. Business rules, ownership and permission checks, and status transitions live here. Services raise domain exceptions and never `HTTPException`.
4. **Repositories**: `app/repositories/`. These subclass `BaseRepository(session)`. Many write methods call `session.commit()` themselves (bookings, favorites, users). Others only `flush()`, and the service calls `repository.commit()` and `rollback()` explicitly so several writes share one transaction (properties, reviews with rating recalculation, chats, property views). Check which pattern the domain you're editing follows before you add a write.
5. **Models**: `app/models/`. These use declarative `Base` (`app/db/base.py`) plus `IDMixin` and `TimestampMixin` (`app/db/mixins.py`). Enums (`UserRole`, `BookingStatus`, `NotificationType`, …) live in `app/db/enums.py`. Every model must be imported in `app/models/__init__.py`. Alembic autogenerate (`import app.models` in `alembic/env.py`) and the test `create_all` both depend on that import. `app/websocket/manager.py` holds in-memory `ConnectionManager` instances (`chat_manager`, `property_viewers_manager`), so WebSocket state is per process and the app runs with one Gunicorn worker. `app/tasks/booking.py` is a background loop started in the `main.py` lifespan (skipped when `ENVIRONMENT=testing`) that expires pending bookings and completes finished stays.
6. **Schemas**: `app/schemas/`. These are Pydantic request and response models. List endpoints use `*ListParams` (page and size) and `*ListResponse` (items, total, page, size, pages). The route computes `pages`.

### Error handling

Each domain defines plain exception classes in `app/exceptions/<domain>.py`. A matching handler function in `app/api/handlers/<domain>.py` maps each class to a status code and a `{"detail": str(exc)}` response. Every exception/handler pair must also be registered in `app/api/handlers/register.py`, or the exception surfaces as a generic 500 (`app/api/handlers/common.py` also maps `IntegrityError` to 409). Some exception names repeat across modules: `PropertyNotFoundException` exists in both `exceptions/booking.py` and `exceptions/property.py`, and these are different classes. Import the one from the domain you're working in, and alias duplicates in `register.py` (a plain second import shadows the first one, which then goes unregistered). Auth exceptions carry default messages, so they can be raised without arguments.

WebSocket routes don't go through these handlers. They `accept()` first, then close with the codes in `app/websocket/codes.py` (4401, 4403, 4404). They authenticate with the `token` query parameter through `get_optional_current_user`.

### Auth

JWT (PyJWT) access and refresh tokens are built in `app/security/jwt.py`, with bcrypt hashing in `app/security/hashing.py`. Login uses the OAuth2 password form at `/api/v1/auth/login`, so tests post `data={"username", "password"}`. Refresh tokens are stored in the DB (`RefreshToken` model with `is_revoked` and a timezone-aware expiry) and are rotated on refresh. Registration accepts `role` `user` or `host` (never `admin`). Inactive users (`is_active=False`) are rejected at login, on refresh, and in `get_current_user`.

### Media

`app/storage/local.py` (`MediaSaver`) writes uploads to `media/properties/<uuid>.<ext>` and stores paths relative to `media/`. `app/main.py` serves them at `/media`. `ImageValidator` in `app/storage/validator.py` validates uploads.

### Tests

Tests are in `app/tests/<domain>/`. Service-level business-logic tests (for example `bookings/test_booking.py`) build repositories and services directly on `db_session`. API tests are in `api/` subfolders and use the `client` fixture, which overrides `get_session` with the test session. Shared fixtures in `conftest.py` include `api_user` with `auth_headers`, `owner` (HOST role) with `owner_auth_headers`, `owner_property`, and `completed_booking`. The `guest` fixture owns the `property` fixture.

WebSocket tests use `open_ws` from `app/tests/ws.py` (httpx-ws in the test's own event loop). A fixture can't do this, because the transport's task group must be entered and exited in the same task. All connections share the single test DB session, so open them one at a time and wait for the first server event (`connected` or `viewers`) before opening the next. Booking tests must use future dates, because `create_booking` rejects check-ins in the past.
