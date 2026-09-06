import os
import uuid

import aiofiles
from fastapi import UploadFile
from pathlib import Path


class MediaSaver:
    MEDIA_DIR = Path("media")
    BASE_DIR = MEDIA_DIR / "properties"

    def __init__(self):
        self.BASE_DIR.mkdir(parents=True, exist_ok=True)

    def _generate_unique_filename(self, original_filename: str) -> str:
        extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{extension}"
        return unique_filename

    async def save_file(self, file: UploadFile) -> str:
        if not file.filename:
            raise ValueError("Filename is required")

        unique_filename = self._generate_unique_filename(file.filename)
        file_path = self.BASE_DIR / unique_filename

        try:
            async with aiofiles.open(file_path, "wb") as buffer:
                while chunk := await file.read(1024 * 1024):
                    await buffer.write(chunk)
        except Exception:
            if file_path.exists():
                file_path.unlink()
            

        return str(file_path.relative_to(self.MEDIA_DIR).as_posix())

    async def delete_file(self, file_path: str) -> None:
        full_path = self.MEDIA_DIR / file_path

        if full_path.exists():
            full_path.unlink()