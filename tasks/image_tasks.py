import io
from PIL import Image
from celery import shared_task
from services.minio_client import minio_client
from config.settings import settings

@shared_task(bind=True)
def resize_image_task(self, filename: str, width: int, height: int):
    """Tarea asíncrona para redimensionar imagen"""
    try:
        # Actualizar estado de la tarea
        self.update_state(
            state="PROGRESS",
            meta={"status": "Descargando imagen desde MinIO..."}
        )
        
        # Descargar imagen desde MinIO
        image_data = minio_client.get_image_data(filename)
        
        self.update_state(
            state="PROGRESS",
            meta={"status": "Procesando imagen..."}
        )
        
        # Procesar imagen
        with Image.open(io.BytesIO(image_data)) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionar manteniendo proporción
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            
            # Guardar en buffer
            buffer = io.BytesIO()
            img.save(buffer, format=img.format or 'JPEG', quality=85)
            buffer.seek(0)
            processed_image_data = buffer.getvalue()
        
        self.update_state(
            state="PROGRESS",
            meta={"status": "Subiendo imagen procesada a MinIO..."}
        )
        
        # Generar nombre para la imagen procesada
        name, ext = filename.rsplit('.', 1)
        processed_filename = f"{name}_resized_{width}x{height}.{ext}"
        
        # Subir imagen procesada a MinIO
        result = minio_client.upload_image(
            file_data=processed_image_data,
            filename=processed_filename,
            content_type="image/jpeg"
        )
        
        # Tarea completada exitosamente
        return {
            "status": "SUCCESS",
            "original_filename": filename,
            "processed_filename": processed_filename,
            "width": width,
            "height": height,
            "size": len(processed_image_data),
            "file_url": result["file_url"]
        }
        
    except Exception as e:
        # Tarea falló
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise e

@shared_task(bind=True)
def process_image_metadata_task(self, filename: str):
    """Tarea asíncrona para extraer metadatos de imagen"""
    try:
        self.update_state(
            state="PROGRESS",
            meta={"status": "Extrayendo metadatos..."}
        )
        
        # Descargar imagen desde MinIO
        image_data = minio_client.get_image_data(filename)
        
        # Procesar con Pillow para obtener metadatos
        with Image.open(io.BytesIO(image_data)) as img:
            metadata = {
                "filename": filename,
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.width,
                "height": img.height,
                "palette": img.palette.mode if img.palette else None,
                "info": img.info
            }
        
        return {
            "status": "SUCCESS",
            "metadata": metadata
        }
        
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise e
