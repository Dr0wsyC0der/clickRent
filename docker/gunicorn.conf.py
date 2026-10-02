import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Состояние WebSocket (рассылка событий, присутствие) синхронизируется через Redis,
# поэтому воркеров может быть несколько
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
worker_class = "uvicorn_worker.UvicornWorker"

timeout = 60
graceful_timeout = 30
keepalive = 5

# Запросы логирует само приложение (RequestLoggingMiddleware)
accesslog = None
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()

# Приложение работает за nginx, доверяем заголовкам X-Forwarded-*
forwarded_allow_ips = "*"

# Управляющий сокет gunicornc не используется (и требует записи в домашний каталог)
control_socket_disable = True
