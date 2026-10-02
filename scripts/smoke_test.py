"""Сквозная проверка запущенного стека docker compose через nginx.

Проверяет основные сценарии и работу нескольких процессов API: WebSocket-подключения
раскидываются nginx и Gunicorn по разным воркерам и репликам, а события, присутствие,
кэш и лимиты должны быть общими через Redis.

Запуск: python scripts/smoke_test.py http://localhost
Зависимости: httpx, websockets, pillow.
"""
import asyncio
import io
import json
import sys
import uuid

import httpx
import websockets
from PIL import Image

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost"
WS_URL = BASE_URL.replace("http://", "ws://", 1).replace("https://", "wss://", 1)
RUN_ID = uuid.uuid4().hex[:6]
PASSWORD = "smoke_password"
VIEWERS = 8
CHAT_ROUNDS = 6


def check(condition: bool, label: str) -> None:
    print(("OK   " if condition else "FAIL ") + label, flush=True)
    if not condition:
        raise SystemExit(1)


def ws_connect(path: str):
    return websockets.connect(f"{WS_URL}{path}", proxy=None, open_timeout=10)


async def drain_last(ws, timeout: float = 0.5) -> dict | None:
    """Последнее событие из уже пришедших в сокет."""
    last = None
    try:
        while True:
            last = json.loads(await asyncio.wait_for(ws.recv(), timeout))
    except asyncio.TimeoutError:
        return last


async def register_and_login(client: httpx.AsyncClient, username: str, role: str) -> tuple[int, str, dict]:
    response = await client.post("/api/v1/auth/register", json={
        "username": username, "email": f"{username}@example.com", "password": PASSWORD, "role": role,
    })
    check(response.status_code == 200, f"регистрация {username} ({role})")
    user_id = response.json()["id"]

    response = await client.post("/api/v1/auth/login", data={"username": username, "password": PASSWORD})
    check(response.status_code == 200, f"вход {username}")
    token = response.json()["access_token"]
    return user_id, token, {"Authorization": f"Bearer {token}"}


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15, trust_env=False) as client:
        response = await client.get("/health/ready")
        check(response.json() == {"status": "ok", "database": "ok", "redis": "ok"}, "readiness: PostgreSQL и Redis")

        host_id, host_token, host = await register_and_login(client, f"smoke_host_{RUN_ID}", "host")
        _, guest_token, guest = await register_and_login(client, f"smoke_guest_{RUN_ID}", "user")

        # --- Объект, изображение, бронирование ---
        response = await client.post("/api/v1/properties/", headers=host, json={
            "title": "Smoke loft", "beds": 2, "bathrooms": 1, "guest_capacity": 3, "rooms": 2,
            "country": "Russia", "city": "Moscow", "address": f"Smoke street, {RUN_ID}", "price_per_night": "120.00",
        })
        check(response.status_code == 201, "хост создал объект")
        property_id = response.json()["id"]

        image = io.BytesIO()
        Image.new("RGB", (32, 32), "red").save(image, format="PNG")
        response = await client.post(
            "/api/v1/property-images/", params={"property_id": property_id}, headers=host,
            files={"file": ("smoke.png", image.getvalue(), "image/png")},
        )
        check(response.status_code == 201, "загрузка изображения")
        response = await client.get(response.json()["image_url"])
        check(response.status_code == 200 and response.headers["content-type"] == "image/png", "nginx отдает /media")

        dates = {"check_in": "2031-05-01T12:00:00Z", "check_out": "2031-05-04T12:00:00Z"}
        response = await client.post("/api/v1/bookings/", headers=guest, json={
            "property_id": property_id, "guests": 2, **dates,
        })
        check(response.status_code == 201 and response.json()["expires_at"], "бронь создана с soft-lock")
        booking_id = response.json()["id"]

        response = await client.post("/api/v1/bookings/", headers=guest, json={"property_id": property_id, **dates})
        check(response.status_code == 409, "пересекающаяся бронь отклонена")

        response = await client.post(f"/api/v1/bookings/{booking_id}/confirm", headers=host)
        check(response.status_code == 204, "хост подтвердил бронь")

        response = await client.get("/api/v1/notifications/", headers=guest)
        check(response.json()["notifications"][0]["type"] == "booking_confirmed", "гость получил уведомление")

        response = await client.get("/api/v1/properties/search", params={"city": "moscow", **dates})
        check(property_id not in [p["id"] for p in response.json()["properties"]], "поиск по датам учитывает бронь")

        # --- Кэш: после изменения все процессы отдают свежие данные ---
        for _ in range(4):
            await client.get(f"/api/v1/properties/{property_id}")
            await client.get("/api/v1/properties/search", params={"city": "moscow"})
        response = await client.patch(f"/api/v1/properties/{property_id}", headers=host, json={"title": "Smoke loft v2"})
        check(response.status_code == 200, "хост обновил объект")
        titles = {(await client.get(f"/api/v1/properties/{property_id}")).json()["title"] for _ in range(8)}
        check(titles == {"Smoke loft v2"}, "карточка из кэша обновлена во всех процессах")
        response = await client.get("/api/v1/properties/search", params={"city": "moscow"})
        check(response.json()["properties"][0]["title"] == "Smoke loft v2", "поиск из кэша обновлен")

        # --- Счетчик зрителей: подключения на разных воркерах видят общий счетчик ---
        viewers = []
        try:
            for _ in range(VIEWERS):
                viewers.append(await ws_connect(f"/api/v1/properties/{property_id}/viewers/ws"))
            await asyncio.sleep(0.5)
            counts = [(await drain_last(ws) or {}).get("count") for ws in viewers]
            check(counts == [VIEWERS] * VIEWERS, f"{VIEWERS} зрителей видят общий счетчик: {counts}")
            response = await client.get(f"/api/v1/properties/{property_id}/signals")
            check(response.json()["viewing_now"] == VIEWERS, "signals.viewing_now учитывает все процессы")
        finally:
            for ws in viewers:
                await ws.close()
        await asyncio.sleep(0.5)
        response = await client.get(f"/api/v1/properties/{property_id}/signals")
        check(response.json()["viewing_now"] == 0, "присутствие очищено после отключения")

        # --- Чат: участники подключаются к случайным воркерам, сообщения доходят ---
        response = await client.post("/api/v1/chats/", headers=guest, json={"participant_id": host_id})
        check(response.status_code == 201, "чат создан")
        chat_id = response.json()["id"]

        delivered = 0
        for attempt in range(CHAT_ROUNDS):
            async with ws_connect(f"/api/v1/chats/{chat_id}/ws?token={guest_token}") as guest_ws, \
                    ws_connect(f"/api/v1/chats/{chat_id}/ws?token={host_token}") as host_ws:
                assert json.loads(await guest_ws.recv())["type"] == "connected"
                assert json.loads(await host_ws.recv())["type"] == "connected"
                await guest_ws.send(json.dumps({"content": f"Сообщение {attempt}"}))
                event = json.loads(await asyncio.wait_for(host_ws.recv(), 5))
                delivered += event["message"]["content"] == f"Сообщение {attempt}"
        check(delivered == CHAT_ROUNDS, f"сообщения доставлены между процессами: {delivered}/{CHAT_ROUNDS}")

        response = await client.get("/api/v1/notifications/", headers=host)
        check(
            all(n["type"] != "new_message" for n in response.json()["notifications"]),
            "онлайн-участник не получает уведомления о сообщениях",
        )

        # --- Формат ошибок и трассировка ---
        response = await client.get("/api/v1/properties/999999")
        check(response.status_code == 404 and response.json()["detail"], "404 в формате {detail}")
        check("x-request-id" in response.headers, "X-Request-ID проброшен через nginx")

        # --- Rate limiting (в конце: блокирует вход с этого IP до конца окна) ---
        statuses = []
        for _ in range(30):
            response = await client.post("/api/v1/auth/login", data={"username": f"smoke_guest_{RUN_ID}", "password": "wrong"})
            statuses.append(response.status_code)
            if response.status_code == 429:
                break
        check(statuses[0] == 401 and statuses[-1] == 429, f"rate limiting входа: {len(statuses)} попыток до 429")
        check(int(response.headers["Retry-After"]) > 0, "заголовок Retry-After")


if __name__ == "__main__":
    asyncio.run(main())
    print("SMOKE PASSED")
