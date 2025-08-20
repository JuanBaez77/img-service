from pydantic import BaseModel
from datetime import datetime
from typing import List

class UploadResponse(BaseModel):
    filename: str
    size: int
    content_type: str

class ImageInfo(BaseModel):
    nombre: str
    tamaño: int
    fecha_creacion: datetime

class ImageListResponse(BaseModel):
    images: List[ImageInfo]
