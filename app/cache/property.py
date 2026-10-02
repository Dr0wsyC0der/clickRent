import hashlib
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel
from redis.asyncio import Redis

from app.core.redis import redis_key
from app.models.properties import Property as PropertyModel
from app.schemas.property import PropertyResponse

logger = logging.getLogger(__name__)

CATALOG_VERSION_KEY = redis_key("cache", "catalog", "version")


class PropertyCache:
    """Кэш карточек объектов и страниц каталога (список, поиск) в Redis.

    Инвалидация версионная: ключ данных содержит номер версии, а изменение объекта увеличивает
    версию (INCR) после коммита. Старые записи больше не читаются и истекают по TTL.
    Версия читается до запроса в БД, поэтому запрос, начавшийся до изменения, сохранит
    результат под старой версией и не перезапишет свежие данные.

    Ключи версий не имеют TTL и не вытесняются политикой volatile-lru. Если Redis недоступен,
    чтение идет напрямую в БД.
    """

    def __init__(self, redis: Redis, enabled: bool, property_ttl_seconds: int, catalog_ttl_seconds: int):
        self.redis = redis
        self.enabled = enabled
        self.property_ttl_seconds = property_ttl_seconds
        self.catalog_ttl_seconds = catalog_ttl_seconds

    async def get_property(
        self,
        property_id: int,
        loader: Callable[[], Awaitable[PropertyModel | None]],
    ) -> PropertyResponse | PropertyModel | None:
        if not self.enabled:
            return await loader()

        version_key = self._property_version_key(property_id)
        try:
            version = await self.redis.get(version_key) or 0
            data_key = redis_key("cache", "property", property_id, f"v{version}")
            cached = await self.redis.get(data_key)
            if cached is not None:
                return PropertyResponse.model_validate_json(cached)
        except Exception:
            logger.warning("Кэш недоступен, объект читается из БД", exc_info=True)
            return await loader()

        property_obj = await loader()
        if property_obj is not None:
            await self._store(data_key, PropertyResponse.model_validate(property_obj).model_dump_json(),
                              self.property_ttl_seconds)
        return property_obj

    async def get_catalog_page(
        self,
        kind: str,
        params: BaseModel,
        loader: Callable[[], Awaitable[tuple[list[PropertyModel], int]]],
    ) -> tuple[list[PropertyResponse] | list[PropertyModel], int]:
        if not self.enabled:
            return await loader()

        try:
            version = await self.redis.get(CATALOG_VERSION_KEY) or 0
            data_key = redis_key("cache", "catalog", f"v{version}", kind, self._params_hash(params))
            cached = await self.redis.get(data_key)
            if cached is not None:
                page = json.loads(cached)
                return [PropertyResponse.model_validate(item) for item in page["items"]], page["total"]
        except Exception:
            logger.warning("Кэш недоступен, каталог читается из БД", exc_info=True)
            return await loader()

        properties, total = await loader()
        payload = {
            "items": [PropertyResponse.model_validate(item).model_dump(mode="json") for item in properties],
            "total": total,
        }
        await self._store(data_key, json.dumps(payload, ensure_ascii=False), self.catalog_ttl_seconds)
        return properties, total

    async def invalidate_property(self, property_id: int) -> None:
        """Изменились данные объекта: сбрасываются его карточка и страницы каталога."""
        await self._bump(self._property_version_key(property_id), CATALOG_VERSION_KEY)

    async def invalidate_catalog(self) -> None:
        """Изменился состав каталога или результаты фильтров (новый объект, удобства)."""
        await self._bump(CATALOG_VERSION_KEY)

    async def _bump(self, *version_keys: str) -> None:
        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                for key in version_keys:
                    pipe.incr(key)
                await pipe.execute()
        except Exception:
            # Устаревшие данные проживут не дольше TTL записи
            logger.error("Не удалось инвалидировать кэш: %s", ", ".join(version_keys), exc_info=True)

    async def _store(self, key: str, value: str, ttl_seconds: int) -> None:
        try:
            await self.redis.set(key, value, ex=ttl_seconds)
        except Exception:
            logger.warning("Не удалось сохранить данные в кэш", exc_info=True)

    @staticmethod
    def _property_version_key(property_id: int) -> str:
        return redis_key("cache", "property", property_id, "version")

    @staticmethod
    def _params_hash(params: BaseModel) -> str:
        serialized: dict[str, Any] = params.model_dump(mode="json")
        return hashlib.sha256(json.dumps(serialized, sort_keys=True).encode()).hexdigest()[:32]
