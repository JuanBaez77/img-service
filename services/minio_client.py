import io
from datetime import datetime, timedelta
from typing import Optional, List
from minio import Minio
from minio.error import S3Error
from PIL import Image
import os

from config.settings import settings

class MinIOClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Asegurar que el bucket existe"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                print(f"Bucket '{self.bucket}' creado exitosamente")
        except S3Error as e:
            print(f"Error creando bucket: {e}")
    
    def upload_image(self, file_data: bytes, filename: str, content_type: str) -> dict:
        """Subir imagen a MinIO"""
        try:
            # Generar nombre único
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{timestamp}{ext}"
            
            # Subir archivo
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=unique_filename,
                data=io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            
            return {
                "filename": unique_filename,
                "bucket": self.bucket,
                "content_type": content_type,
                "size": len(file_data),
                "file_url": f"minio://{self.bucket}/{unique_filename}"
            }
        except S3Error as e:
            raise Exception(f"Error subiendo imagen a MinIO: {e}")
    
    def get_image_url(self, filename: str, expiry: int = None) -> str:
        """Obtener URL firmada para descargar imagen"""
        try:
            if expiry is None:
                expiry = settings.SIGNED_URL_EXPIRY
            
            url = self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=filename,
                expires=timedelta(seconds=expiry)
            )
            return url
        except S3Error as e:
            raise Exception(f"Error generando URL firmada: {e}")
    
    def list_images(self) -> List[dict]:
        """Listar todas las imágenes con metadatos"""
        try:
            images = []
            objects = self.client.list_objects(self.bucket, recursive=True)
            
            for obj in objects:
                if any(obj.object_name.lower().endswith(ext) for ext in settings.ALLOWED_EXTENSIONS):
                    # Obtener metadatos del objeto
                    stat = self.client.stat_object(self.bucket, obj.object_name)
                    
                    images.append({
                        "nombre": obj.object_name,
                        "tamaño": stat.size,
                        "fecha_creacion": stat.last_modified,
                        "content_type": stat.content_type,
                        "etag": stat.etag
                    })
            
            # Ordenar por fecha de creación (más reciente primero)
            images.sort(key=lambda x: x["fecha_creacion"], reverse=True)
            return images
            
        except S3Error as e:
            raise Exception(f"Error listando imágenes: {e}")
    
    def delete_image(self, filename: str) -> bool:
        """Eliminar imagen de MinIO"""
        try:
            self.client.remove_object(self.bucket, filename)
            return True
        except S3Error as e:
            raise Exception(f"Error eliminando imagen: {e}")
    
    def image_exists(self, filename: str) -> bool:
        """Verificar si una imagen existe"""
        try:
            self.client.stat_object(self.bucket, filename)
            return True
        except S3Error:
            return False
    
    def get_image_data(self, filename: str) -> bytes:
        """Obtener datos de la imagen"""
        try:
            response = self.client.get_object(self.bucket, filename)
            return response.read()
        except S3Error as e:
            raise Exception(f"Error obteniendo imagen: {e}")

# Instancia global del cliente
minio_client = MinIOClient()
