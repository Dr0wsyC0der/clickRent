import logging

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.api.dependencies.redis import get_redis_client
from app.core.config import settings
from app.core.rate_limit import RateLimitRule, hit
from app.exceptions.rate_limit import RateLimitExceededException

logger = logging.getLogger(__name__)


def client_ip(request: Request) -> str:
    # За nginx адрес клиента восстанавливается из X-Forwarded-For (proxy headers в Uvicorn)
    return request.client.host if request.client else "unknown"


def rate_limit(scope: str):
    """Зависимость FastAPI: лимит запросов с одного IP для эндпоинта.

    Правило читается из настроек `rate_limit_<scope>` при каждом запросе. Если Redis недоступен,
    запрос пропускается: недоступность кэша лимитов не должна останавливать вход в систему.
    """

    async def dependency(request: Request, redis: Redis = Depends(get_redis_client)) -> None:
        if not settings.rate_limit_enabled:
            return

        rule = RateLimitRule.parse(getattr(settings, f"rate_limit_{scope}"))
        try:
            retry_after = await hit(redis, scope, client_ip(request), rule)
        except Exception:
            logger.warning("Rate limiting недоступен: ошибка Redis, запрос пропущен", exc_info=True)
            return

        if retry_after is not None:
            logger.warning("Превышен лимит запросов %s для %s", scope, client_ip(request))
            raise RateLimitExceededException(retry_after)

    return dependency
