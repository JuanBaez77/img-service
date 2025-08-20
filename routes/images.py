import os
import shutil
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, Response
from PIL import Image
import io

from models import UploadResponse, ImageInfo, ImageListResponse

router = APIRouter()

# Configuración
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

# Crear directorio de uploads si no existe
os.makedirs(UPLOAD_DIR, exist_ok=True)

def is_valid_image(filename: str) -> bool:
    """Verificar si el archivo es una imagen válida"""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

def get_file_info(filename: str) -> ImageInfo:
    """Obtener información de un archivo"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    stat = os.stat(file_path)
    return ImageInfo(
        nombre=filename,
        tamaño=stat.st_size,
        fecha_creacion=datetime.fromtimestamp(stat.st_ctime)
    )

@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """Subir una imagen"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo no proporcionado")
    
    if not is_valid_image(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"Formato de archivo no válido. Formatos permitidos: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generar nombre único para evitar conflictos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(file.filename)
    unique_filename = f"{name}_{timestamp}{ext}"
    
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Obtener información del archivo
        file_size = os.path.getsize(file_path)
        
        return UploadResponse(
            filename=unique_filename,
            size=file_size,
            content_type=file.content_type or "application/octet-stream"
        )
    
    except Exception as e:
        # Limpiar archivo en caso de error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")

@router.get("/images", response_model=ImageListResponse)
async def list_images():
    """Listar todas las imágenes almacenadas"""
    try:
        images = []
        for filename in os.listdir(UPLOAD_DIR):
            if is_valid_image(filename):
                image_info = get_file_info(filename)
                images.append(image_info)
        
        # Ordenar por fecha de creación (más reciente primero)
        images.sort(key=lambda x: x.fecha_creacion, reverse=True)
        
        return ImageListResponse(images=images)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar imágenes: {str(e)}")

@router.get("/images/{filename}")
async def get_image(filename: str):
    """Obtener una imagen específica"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    if not is_valid_image(filename):
        raise HTTPException(status_code=400, detail="Formato de archivo no válido")
    
    return FileResponse(file_path, media_type="image/*")

@router.get("/resize/{filename}")
async def resize_image(
    filename: str,
    width: int = Query(..., gt=0, description="Ancho de la imagen"),
    height: int = Query(..., gt=0, description="Alto de la imagen")
):
    """Devolver la imagen redimensionada"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    if not is_valid_image(filename):
        raise HTTPException(status_code=400, detail="Formato de archivo no válido")
    
    try:
        # Abrir y redimensionar imagen
        with Image.open(file_path) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionar manteniendo proporción
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            
            # Guardar en buffer
            buffer = io.BytesIO()
            img.save(buffer, format=img.format or 'JPEG', quality=85)
            buffer.seek(0)
            
            # Convertir buffer a bytes para la respuesta
            image_bytes = buffer.getvalue()
            
            return Response(
                content=image_bytes,
                media_type="image/*",
                headers={"Content-Disposition": f"attachment; filename=resized_{filename}"}
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar imagen: {str(e)}")

@router.delete("/images/{filename}")
async def delete_image(filename: str):
    """Borrar una imagen"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    if not is_valid_image(filename):
        raise HTTPException(status_code=400, detail="Formato de archivo no válido")
    
    try:
        os.remove(file_path)
        return {"message": f"Archivo {filename} eliminado correctamente"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar archivo: {str(e)}")
