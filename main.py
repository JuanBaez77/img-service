from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import images
from config.settings import settings

app = FastAPI(
    title="API de Gestión de Imágenes - Nivel Intermedio",
    description="Microservicio para gestión de imágenes con FastAPI, MinIO y Celery",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(images.router, prefix="/api/v1", tags=["imágenes"])

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "API de Gestión de Imágenes",
        "version": "2.0.0",
        "features": [
            "Almacenamiento en MinIO (compatible con S3)",
            "Procesamiento asíncrono con Celery",
            "URLs firmadas para descarga segura",
            "Redimensionado de imágenes en background",
            "Metadatos de imágenes",
            "Cola de tareas con Redis"
        ],
        "endpoints": {
            "upload": "/api/v1/upload",
            "list_images": "/api/v1/images",
            "get_image_url": "/api/v1/images/{filename}",
            "get_image_proxy": "/api/v1/images/{filename}/proxy",
            "get_image_thumbnail": "/api/v1/images/{filename}/thumbnail?width=X&height=Y",
            "resize_image": "/api/v1/resize/{filename}",
            "task_status": "/api/v1/tasks/{task_id}",
            "delete_image": "/api/v1/images/{filename}"
        },
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {
        "status": "healthy", 
        "service": "image-management-api-intermediate",
        "storage": "MinIO",
        "queue": "Celery + Redis"
    }

@app.get("/config")
async def get_config():
    """Obtener configuración del servicio (sin credenciales sensibles)"""
    return {
        "minio_endpoint": settings.MINIO_ENDPOINT,
        "minio_bucket": settings.MINIO_BUCKET,
        "redis_host": settings.REDIS_HOST,
        "redis_port": settings.REDIS_PORT,
        "max_file_size_mb": settings.MAX_FILE_SIZE / (1024*1024),
        "signed_url_expiry_seconds": settings.SIGNED_URL_EXPIRY,
        "allowed_extensions": list(settings.ALLOWED_EXTENSIONS)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.API_HOST, 
        port=settings.API_PORT
    )
