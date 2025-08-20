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

@router.get("/images/{filename}/proxy")
async def get_image_proxy(filename: str):
    """Servir imagen directamente desde MinIO (evita problemas de CORS)"""
    try:
        if not minio_client.image_exists(filename):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        if not is_valid_image(filename):
            raise HTTPException(status_code=400, detail="Formato de archivo no válido")
        
        # Obtener datos de la imagen desde MinIO
        image_data = minio_client.get_image_data(filename)
        
        # Obtener content-type de MinIO
        stat = minio_client.client.stat_object(minio_client.bucket, filename)
        content_type = stat.content_type or "image/*"
        
        # Servir imagen con headers apropiados para CORS
        return Response(
            content=image_data,
            media_type=content_type,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Cache-Control": "public, max-age=3600",  # Cache por 1 hora
                "Content-Disposition": f"inline; filename={filename}"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo imagen: {str(e)}")

@router.options("/images/{filename}/proxy")
async def options_image_proxy(filename: str):
    """Endpoint OPTIONS para CORS preflight"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"  # Cache preflight por 24 horas
        }
    )

@router.get("/images/{filename}/thumbnail")
async def get_image_thumbnail(
    filename: str, 
    width: int = Query(100, gt=0, le=1000, description="Ancho del thumbnail"),
    height: int = Query(100, gt=0, le=1000, description="Alto del thumbnail")
):
    """Obtener thumbnail de imagen (procesamiento síncrono para previews)"""
    try:
        if not minio_client.image_exists(filename):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        if not is_valid_image(filename):
            raise HTTPException(status_code=400, detail="Formato de archivo no válido")
        
        # Obtener datos de la imagen desde MinIO
        image_data = minio_client.get_image_data(filename)
        
        # Procesar imagen para thumbnail
        with Image.open(io.BytesIO(image_data)) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionar manteniendo proporción
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            
            # Guardar en buffer
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            thumbnail_data = buffer.getvalue()
        
        # Servir thumbnail con headers CORS
        return Response(
            content=thumbnail_data,
            media_type="image/jpeg",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Cache-Control": "public, max-age=3600",
                "Content-Disposition": f"inline; filename=thumb_{filename}"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando thumbnail: {str(e)}")

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
