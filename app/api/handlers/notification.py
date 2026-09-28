from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.notification import (
    NotificationNotFoundException
)   

async def notification_not_found_handler(request: Request, exc: NotificationNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )

