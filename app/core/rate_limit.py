import time
from dataclasses import dataclass

from redis.asyncio import Redis

from app.core.redis import redis_key

PERIODS = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}


@dataclass(frozen=True)
class RateLimitRule:
    limit: int
    period_seconds: int

    @classmethod
    def parse(cls, value: str) -> "RateLimitRule":
        """Разбирает лимит вида "10/minute" (second, minute, hour, day) или "10/30" (период в секундах)."""
        try:
            limit, period = value.strip().split("/")
            period = period.strip().lower()
            rule = cls(int(limit), PERIODS[period] if period in PERIODS else int(period))
        except (ValueError, KeyError):
            raise ValueError(
                f"Некорректный лимит '{value}': ожидается '<количество>/<second|minute|hour|day|секунды>'"
            ) from None
        if rule.limit <= 0 or rule.period_seconds <= 0:
            raise ValueError(f"Некорректный лимит '{value}': количество и период должны быть больше нуля")
        return rule


async def hit(redis: Redis, scope: str, identifier: str, rule: RateLimitRule) -> int | None:
    """Учитывает запрос в окне фиксированной длины. Возвращает время до сброса окна,
    если лимит превышен, иначе None."""
    now = time.time()
    window = int(now // rule.period_seconds)
    key = redis_key("ratelimit", scope, identifier, window)

    async with redis.pipeline(transaction=True) as pipe:
        pipe.incr(key)
        pipe.expire(key, rule.period_seconds, nx=True)
        count, _ = await pipe.execute()

    if count <= rule.limit:
        return None
    return max(1, int((window + 1) * rule.period_seconds - now) + 1)
