from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.property_image import (
    PropertyImageNotFoundException,
    PropertyImageCreateException
)   

async def property_image_not_found_handler(request: Request, exc: PropertyImageNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Изображение недвижимости не найдено"},
    )

async def property_image_create_exception_handler(request: Request, exc: PropertyImageCreateException):
    return JSONResponse(
        status_code=400,
        content={"detail": "Ошибка при добавлении изображения"},
    )