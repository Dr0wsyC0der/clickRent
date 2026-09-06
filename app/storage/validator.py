import io

from fastapi import UploadFile, HTTPException
from PIL import Image, UnidentifiedImageError


class ImageValidator:
    ALLOWED_MIMES = {"image/jpeg", "image/png", "image/webp"}
    ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
    MAX_SIZE = 5 * 1024 * 1024  # 5 МБ

    async def validate(self, file: UploadFile) -> dict:
        if file.content_type not in self.ALLOWED_MIMES:
            raise HTTPException(
                status_code=415,
                detail=(
                    f"Unsupported media type. "
                    f"Allowed: {', '.join(self.ALLOWED_MIMES)}"
                ),
            )

        data = await file.read()

        try:
            if len(data) > self.MAX_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"File too large. "
                        f"Max size: {self.MAX_SIZE // (1024 * 1024)} MB"
                    ),
                )

            try:
                img = Image.open(io.BytesIO(data))
                img.verify()
            except (UnidentifiedImageError, OSError):
                raise HTTPException(
                    status_code=415,
                    detail="File is not a valid image",
                )
            img = Image.open(io.BytesIO(data))

            if img.format not in self.ALLOWED_FORMATS:
                raise HTTPException(
                    status_code=415,
                    detail=(
                        f"Unsupported image format. "
                        f"Allowed: {', '.join(self.ALLOWED_FORMATS)}"
                    ),
                )

            return {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(data),
                "format": img.format,
                "width": img.width,
                "height": img.height,
            }

        finally:
            await file.seek(0)