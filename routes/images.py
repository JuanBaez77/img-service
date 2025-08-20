import os
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body
from fastapi.responses import Response
from PIL import Image
import io

from models import (
    UploadResponse, ImageInfo, ImageListResponse, 
    ResizeRequest, ResizeResponse, TaskStatus
)
from services.minio_client import minio_client
from tasks.image_tasks import resize_image_task
from config.settings import settings

router = APIRouter()

def is_valid_image(filename: str) -> bool:
    """Verificar si el archivo es una imagen válida"""
    return any(filename.lower().endswith(ext) for ext in settings.ALLOWED_EXTENSIONS)

def validate_file_size(file_size: int) -> bool:
    """Validar tamaño del archivo"""
    return file_size <= settings.MAX_FILE_SIZE

@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """Subir una imagen a MinIO"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo no proporcionado")
    
    if not is_valid_image(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"Formato de archivo no válido. Formatos permitidos: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    try:
        # Leer contenido del archivo
        file_content = await file.read()
        
        # Validar tamaño
        if not validate_file_size(len(file_content)):
            raise HTTPException(
                status_code=400,
                detail=f"Archivo demasiado grande. Tamaño máximo: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Subir a MinIO
        result = minio_client.upload_image(
            file_data=file_content,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream"
        )
        
        return UploadResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")

@router.get("/images", response_model=ImageListResponse)
async def list_images():
    """Listar todas las imágenes almacenadas en MinIO"""
    try:
        images_data = minio_client.list_images()
        
        # Convertir a modelos Pydantic
        images = []
        for img_data in images_data:
            image_info = ImageInfo(
                nombre=img_data["nombre"],
                tamaño=img_data["tamaño"],
                fecha_creacion=img_data["fecha_creacion"],
                content_type=img_data.get("content_type"),
                etag=img_data.get("etag")
            )
            images.append(image_info)
        
        return ImageListResponse(images=images)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar imágenes: {str(e)}")

@router.get("/images/{filename}")
async def get_image_url(filename: str):
    """Obtener URL firmada para descargar imagen"""
    try:
        if not minio_client.image_exists(filename):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        if not is_valid_image(filename):
            raise HTTPException(status_code=400, detail="Formato de archivo no válido")
        
        # Generar URL firmada
        signed_url = minio_client.get_image_url(filename)
        
        return {
            "filename": filename,
            "signed_url": signed_url,
            "expires_in": f"{settings.SIGNED_URL_EXPIRY} segundos"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo URL: {str(e)}")

@router.post("/resize/{filename}", response_model=ResizeResponse)
async def resize_image(
    filename: str,
    resize_request: ResizeRequest = Body(...)
):
    """Iniciar redimensionado asíncrono de imagen"""
    try:
        if not minio_client.image_exists(filename):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        if not is_valid_image(filename):
            raise HTTPException(status_code=400, detail="Formato de archivo no válido")
        
        # Validar dimensiones
        if resize_request.width <= 0 or resize_request.height <= 0:
            raise HTTPException(status_code=400, detail="Dimensiones deben ser positivas")
        
        # Iniciar tarea asíncrona
        from tasks.image_tasks import resize_image_task
        task = resize_image_task.delay(
            filename=filename,
            width=resize_request.width,
            height=resize_request.height
        )
        
        return ResizeResponse(
            task_id=task.id,
            message="Tarea de redimensionado iniciada",
            status_url=f"/api/v1/tasks/{task.id}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error iniciando redimensionado: {str(e)}")

@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Obtener estado de una tarea"""
    try:
        from celery_app import celery_app
        
        task = celery_app.AsyncResult(task_id)
        
        if task.state == "PENDING":
            return TaskStatus(
                task_id=task_id,
                status="PENDING",
                progress="Tarea en cola"
            )
        elif task.state == "PROGRESS":
            return TaskStatus(
                task_id=task_id,
                status="PROGRESS",
                progress=task.info.get("status", "Procesando...")
            )
        elif task.state == "SUCCESS":
            return TaskStatus(
                task_id=task_id,
                status="SUCCESS",
                result=task.result
            )
        elif task.state == "FAILURE":
            return TaskStatus(
                task_id=task_id,
                status="FAILURE",
                error=str(task.info)
            )
        else:
            return TaskStatus(
                task_id=task_id,
                status=task.state,
                progress="Estado desconocido"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado de tarea: {str(e)}")

@router.delete("/images/{filename}")
async def delete_image(filename: str):
    """Eliminar imagen de MinIO"""
    try:
        if not minio_client.image_exists(filename):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        if not is_valid_image(filename):
            raise HTTPException(status_code=400, detail="Formato de archivo no válido")
        
        minio_client.delete_image(filename)
        return {"message": f"Archivo {filename} eliminado correctamente de MinIO"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar archivo: {str(e)}")
