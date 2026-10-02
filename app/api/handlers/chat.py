from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.chat import (
    ChatNotFoundException,
    ChatAccessDeniedException,
    ChatParticipantNotFoundException,
    InvalidChatParticipantException,
)

async def chat_not_found_handler(request: Request, exc: ChatNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )

async def chat_access_denied_handler(request: Request, exc: ChatAccessDeniedException):
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc)},
    )

async def chat_participant_not_found_handler(request: Request, exc: ChatParticipantNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )

async def invalid_chat_participant_handler(request: Request, exc: InvalidChatParticipantException):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )
