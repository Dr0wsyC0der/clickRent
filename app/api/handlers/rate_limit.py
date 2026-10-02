from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.rate_limit import RateLimitExceededException

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceededException):
    return JSONResponse(
        status_code=429,
        content={"detail": str(exc)},
        headers={"Retry-After": str(exc.retry_after)},
    )
