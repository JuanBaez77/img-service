from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UploadResponse(BaseModel):
    filename: str
    bucket: str
    content_type: str
    size: int
    file_url: str

class ImageInfo(BaseModel):
    nombre: str
    tamaño: int
    fecha_creacion: datetime
    content_type: Optional[str] = None
    etag: Optional[str] = None

class ImageListResponse(BaseModel):
    images: List[ImageInfo]

class ResizeRequest(BaseModel):
    width: int
    height: int

class ResizeResponse(BaseModel):
    task_id: str
    message: str
    status_url: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    progress: Optional[str] = None

class ImageMetadata(BaseModel):
    filename: str
    format: Optional[str] = None
    mode: Optional[str] = None
    size: Optional[tuple] = None
    width: Optional[int] = None
    height: Optional[int] = None
    palette: Optional[str] = None
    info: Optional[dict] = None
