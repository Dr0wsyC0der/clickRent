# ClickRent

Асинхронный backend сервиса краткосрочной аренды жилья: объекты недвижимости, бронирования с защитой от двойного бронирования, отзывы, избранное, уведомления, чат в реальном времени и социальные сигналы («сейчас смотрят N человек»).

[![CI](https://github.com/Dr0wsyC0der/clickRent/actions/workflows/ci.yml/badge.svg)](https://github.com/Dr0wsyC0der/clickRent/actions/workflows/ci.yml)

## Возможности

- **Пользователи и роли.** Регистрация гостя или владельца (`host`), JWT access/refresh с ротацией и отзывом refresh-токенов, вход по username, email или телефону, деактивация учетных записей.
- **Недвижимость.** CRUD для владельцев, удобства (amenities), загрузка изображений с валидацией, учет уникальных просмотров (пользователь или анонимный посетитель, раз в день).
- **Поиск.** Город и страна (без учета регистра), цена min/max, количество гостей, комнат, кроватей и ванных, минимальный рейтинг, набор удобств, доступность по датам. Сортировка по цене, рейтингу, популярности и дате.
- **Бронирования.** Soft-lock дат на время ожидания подтверждения (TTL), защита от конкурентного бронирования, подтверждение и отклонение владельцем, отмена гостем, автоматическое истечение и завершение.
- **Отзывы.** Только после состоявшегося проживания, один отзыв на бронь, автоматический пересчет рейтинга объекта.
- **Чат.** Личные чаты гостя и владельца через WebSocket и REST, история сообщений, проверка участников.
- **Социальные сигналы.** Счетчик зрителей объекта в реальном времени и агрегаты: просмотры, добавления в избранное, недавние бронирования.
- **Уведомления.** Новая бронь, подтверждение, отмена или отклонение, истечение, завершение проживания, новый отзыв, новое сообщение.

## Стек

Python 3.12, FastAPI, SQLAlchemy 2.0 (async, asyncpg), PostgreSQL 17, Alembic, Pydantic v2, PyJWT, Gunicorn + Uvicorn, nginx, Docker Compose, pytest, httpx-ws, ruff, GitHub Actions.

## Архитектура

Запрос проходит через слои, каждый слой разбит по доменам (booking, property, review, chat, …):

```
routes  →  dependencies  →  services  →  repositories  →  models
(HTTP/WS)   (DI, сессия)     (бизнес-     (SQL-запросы)    (SQLAlchemy)
                              правила)
```

| Слой | Каталог | Ответственность |
|---|---|---|
| Routes | `app/api/v1/routes/<domain>/` | Тонкие обработчики HTTP и WebSocket, по одному вызову сервиса |
| Dependencies | `app/api/dependencies/` | Сессия БД на запрос, сборка репозиториев и сервисов, `get_current_user`, `check_host`, `check_admin` |
| Services | `app/services/` | Бизнес-правила, проверки прав, переходы статусов. Бросают доменные исключения, а не `HTTPException` |
| Repositories | `app/repositories/` | Запросы к БД поверх `BaseRepository(session)` |
| Models / Schemas | `app/models/`, `app/schemas/` | ORM-модели и Pydantic-схемы запросов и ответов |
| Errors | `app/exceptions/`, `app/api/handlers/` | Доменные исключения и их отображение в HTTP-коды (`{"detail": "..."}`) |
| WebSocket | `app/websocket/` | Менеджер подключений по комнатам (чат, зрители объекта) |
| Tasks | `app/tasks/` | Фоновая обработка бронирований (истечение soft-lock, завершение проживаний) |

```
app/
├── api/            # routes, dependencies, exception handlers
├── core/           # настройки, логирование
├── db/             # Base, миксины, enum'ы, engine
├── exceptions/     # доменные исключения
├── middleware/     # логирование запросов, X-Request-ID
├── models/  repositories/  schemas/  services/
├── storage/        # сохранение и валидация изображений
├── tasks/          # фоновые задачи
├── websocket/      # менеджер подключений, коды закрытия
└── tests/
alembic/            # миграции
docker/             # entrypoint, конфиг gunicorn, init-скрипт Postgres
nginx/              # конфиг reverse proxy
```

## Быстрый старт (Docker)

```bash
cp .env.example .env
# задайте SECRET_KEY: python -c "import secrets; print(secrets.token_urlsafe(32))"
docker compose up -d --build
```

- API: http://localhost/api/v1
- Swagger UI: http://localhost/docs
- Healthcheck: http://localhost/health и http://localhost/health/ready

При старте контейнер `app` применяет миграции (`alembic upgrade head`), поэтому проект поднимается с чистой БД без ручных шагов. Состав стека:

| Сервис | Назначение |
|---|---|
| `db` | PostgreSQL 17, при первой инициализации создает также базу `clickrent_test` |
| `app` | Gunicorn с `UvicornWorker`, слушает 8000 внутри сети compose |
| `nginx` | Reverse proxy на `HTTP_PORT` (по умолчанию 80), проксирование WebSocket, раздача `/media` |

Порты меняются через `POSTGRES_PORT` и `HTTP_PORT` в `.env`.

> Если раньше Postgres запускался из старой версии `docker-compose.yml` (сервис `postgres`), один раз выполните `docker compose up -d --remove-orphans`. Данные сохранятся, том тот же.

## Локальная разработка

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # DATABASE_URL указывает на localhost

docker compose up -d db            # только база
alembic upgrade head
uvicorn app.main:app --reload
```

Все команды запускаются из корня репозитория: приложение читает `./.env` и монтирует `media/` относительно текущего каталога.

### Миграции

```bash
alembic upgrade head
alembic revision --autogenerate -m "описание"
alembic check                      # модели и миграции совпадают
```

`alembic/env.py` берет URL из `settings.database_url`. Каждая новая модель импортируется в `app/models/__init__.py`, иначе autogenerate и тесты ее не увидят.

### Тесты и проверка кода

```bash
pytest app/tests
pytest app/tests/bookings/test_booking_lifecycle.py::test_concurrent_bookings_only_one_succeeds
ruff check .
```

Тестам нужна существующая база `clickrent_test`. Docker-образ Postgres создает ее автоматически, URL переопределяется переменной `TEST_DATABASE_URL`. Каждый тест создает таблицы через `Base.metadata.create_all` и удаляет их после себя. WebSocket тестируется через `httpx-ws` в том же event loop, что и сессия БД (хелпер `app/tests/ws.py`).

## Конфигурация

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DATABASE_URL` | — | `postgresql+asyncpg://...`, в compose переопределяется на хост `db` |
| `SECRET_KEY`, `ALGORITHM` | — | Подпись JWT (`HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` | — | Время жизни токенов |
| `ENVIRONMENT` | `development` | `development` / `production` / `testing` (в `testing` фоновая задача не запускается) |
| `LOG_LEVEL` | `INFO` | Уровень логирования |
| `SQL_ECHO` | `false` | Логировать SQL-запросы |
| `BOOKING_PENDING_TTL_MINUTES` | `30` | Сколько pending-бронь удерживает даты |
| `BOOKING_TASKS_INTERVAL_SECONDS` | `60` | Период фоновой обработки бронирований |
| `WEB_CONCURRENCY` | `1` | Количество воркеров Gunicorn (см. ограничения) |
| `POSTGRES_*`, `POSTGRES_PORT`, `HTTP_PORT` | см. `.env.example` | Параметры docker compose |

## API

Полная интерактивная документация доступна в `/docs`. Авторизация: заголовок `Authorization: Bearer <access_token>`. Логин принимает форму OAuth2 (`username`, `password`).

| Группа | Эндпоинты |
|---|---|
| Auth | `POST /auth/register` (`role`: `user` или `host`), `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` |
| Users | `GET /users/me`, `PATCH /users/me` |
| Properties | `GET /properties/`, `GET /properties/search`, `GET /properties/{id}`, `POST/PATCH/DELETE` (host), `GET /properties/host`, удобства объекта `/properties/{id}/amenities/...` |
| Signals | `GET /properties/{id}/signals`, WS `/properties/{id}/viewers/ws` |
| Images | `POST /property-images/?property_id=`, `GET /property-images/{property_id}`, `DELETE /property-images/{image_id}` |
| Amenities | `GET /amenities/`, `GET /amenities/{id}`, `POST/PATCH/DELETE` (admin) |
| Bookings | `POST /bookings/`, `GET /bookings/my`, `GET /bookings/host` (host, фильтр `status`), `GET /bookings/{id}`, `POST /bookings/{id}/confirm`, `POST /bookings/{id}/cancel`, `GET /bookings/` (admin) |
| Reviews | `POST /reviews/`, `GET /reviews/property/{property_id}`, `GET/PATCH/DELETE /reviews/{id}` |
| Favorites | `POST/DELETE /favorites/{property_id}`, `GET /favorites/` |
| Notifications | `GET /notifications/`, `GET/DELETE /notifications/{id}`, `PATCH /notifications/{id}/read`, `PATCH /notifications/read-all` |
| Chats | `POST /chats/`, `GET /chats/`, `GET /chats/{id}`, `GET/POST /chats/{id}/messages`, WS `/chats/{id}/ws` |
| Health | `GET /health` (liveness), `GET /health/ready` (БД доступна, иначе 503) |

Все пути, кроме health, начинаются с `/api/v1`. Списки поддерживают `page` и `size` и возвращают `total`, `page`, `size`, `pages`. Ошибки приходят в формате `{"detail": "..."}`.

### Поиск

`GET /api/v1/properties/search?city=moscow&min_price=50&max_price=200&guest_capacity=2&rooms=1&amenity_ids=1&amenity_ids=3&check_in=2031-05-01T12:00:00Z&check_out=2031-05-04T12:00:00Z&sort_by=price_asc`

- `amenity_ids`: у объекта должны быть все перечисленные удобства.
- `check_in` и `check_out` задаются вместе. Объект исключается, если даты пересекаются с подтвержденной бронью или с pending-бронью, у которой еще не истек soft-lock.
- `sort_by` принимает `price_asc`, `price_desc`, `rating` (объекты без рейтинга в конце), `popularity` (уникальные просмотры за 30 дней) и `newest` (по умолчанию).

### Жизненный цикл бронирования

```
            создание (soft-lock на TTL)
                     │
                     ▼
  ┌───────────── PENDING ─────────────┐
  │ владелец          │ TTL истек     │ гость отменил /
  │ подтвердил        ▼               │ владелец отклонил
  ▼                EXPIRED            ▼
CONFIRMED ─────────────────────────► CANCELLED
  │  дата выезда прошла          (до даты заезда)
  ▼
COMPLETED  →  можно оставить отзыв
```

- **Soft-lock.** Новая бронь получает `expires_at = now + BOOKING_PENDING_TTL_MINUTES` и до этого момента блокирует даты. Если владелец не подтвердил бронь вовремя, даты освобождаются сразу (проверки учитывают `expires_at`), а фоновая задача переводит бронь в `EXPIRED` и уведомляет гостя.
- **Конкурентность.** Перед проверкой пересечений строка объекта блокируется через `SELECT ... FOR UPDATE`, поэтому параллельные запросы на те же даты выполняются по очереди и успешен только первый (это покрыто тестом с `asyncio.Barrier`). Переходы статусов делаются условным `UPDATE ... WHERE status = ...`, без гонок с фоновой задачей.
- **Проверки.** Даты не в прошлом, минимум одна ночь, `guests` не больше вместимости объекта.
- **Отзыв.** Доступен для `COMPLETED` или для `CONFIRMED` после даты выезда. Рейтинг объекта пересчитывается в той же транзакции.

## WebSocket

Браузер не может передать заголовок `Authorization` в WebSocket, поэтому access-токен передается query-параметром `token`.

### Чат: `/api/v1/chats/{chat_id}/ws?token=<access_token>`

Сначала создайте чат: `POST /api/v1/chats/ {"participant_id": <id>}`. Повторный вызов вернет тот же чат.

```js
const ws = new WebSocket(`ws://localhost/api/v1/chats/${chatId}/ws?token=${accessToken}`);
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.onopen = () => ws.send(JSON.stringify({ content: "Здравствуйте! Свободно на выходных?" }));
```

| Направление | Сообщение |
|---|---|
| сервер → клиент | `{"type": "connected", "chat_id": 1}` после успешной авторизации |
| клиент → сервер | `{"content": "текст"}` (1–2000 символов) |
| сервер → все участники | `{"type": "message", "message": {"id", "chat_id", "sender_id", "content", "created_at"}}` |
| сервер → клиент | `{"type": "error", "detail": "..."}` при некорректном сообщении, соединение остается открытым |

Сообщения сохраняются в БД, история доступна через `GET /chats/{id}/messages` (от новых к старым). Сообщение, отправленное через REST, тоже рассылается подключенным участникам. Уведомление `new_message` получает только участник, у которого этот чат сейчас не открыт.

### Зрители объекта: `/api/v1/properties/{property_id}/viewers/ws[?token=...]`

Анонимное подключение тоже разрешено. При каждом входе и выходе зрителя всем подключенным приходит `{"type": "viewers", "property_id": 1, "count": 3}`. Пользователь с несколькими вкладками считается один раз.

### Коды закрытия

| Код | Причина |
|---|---|
| `4401` | Нет токена или токен недействителен |
| `4403` | Пользователь не участник чата |
| `4404` | Чат или объект не найден |

## Production

- **Gunicorn + UvicornWorker** (`docker/gunicorn.conf.py`), непривилегированный пользователь в контейнере, `HEALTHCHECK` по `/health/ready`.
- **nginx** проксирует API и WebSocket (`Upgrade`, `proxy_read_timeout 1h`), отдает `/media` из общего тома и пробрасывает `X-Request-ID`.
- **Логирование.** Каждый запрос логируется строкой `METHOD path status duration request_id`, `X-Request-ID` возвращается в ответе.
- **Ошибки.** Доменные исключения превращаются в 4xx, `IntegrityError` в 409, необработанные исключения в 500 `{"detail": "Внутренняя ошибка сервера."}` с трассировкой в логе.

### Ограничения

- Состояние WebSocket (подключения чата и счетчик зрителей) хранится в памяти процесса, поэтому по умолчанию работает один воркер (`WEB_CONCURRENCY=1`). Для горизонтального масштабирования `ConnectionManager` нужно заменить на брокер, например Redis Pub/Sub.
- Изображения хранятся на локальном диске (том `media_data`).

## CI/CD

`.github/workflows/ci.yml` запускается на push в `main` и на pull request:

1. **lint**: `ruff check .` и компиляция модулей;
2. **test**: Postgres 17, миграции на чистой БД, `alembic check`, полный `downgrade base` и `upgrade head`, затем `pytest`;
3. **docker**: сборка образа, запуск контейнера с Postgres и ожидание успешного `/health/ready`.
