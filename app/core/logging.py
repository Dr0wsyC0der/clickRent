import logging


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        force=True,
    )
    # Запросы логирует RequestLoggingMiddleware, access-лог uvicorn дублировал бы их
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
