Quiero que generes el código completo de un microservicio en Python usando FastAPI para gestionar imágenes.

Requisitos:

El servicio debe conectarse a MinIO (compatible con S3) como almacenamiento principal.

Endpoints necesarios:

POST /upload: subir imagen.

Recibe archivo vía multipart/form-data.

Lo sube a MinIO.

Devuelve JSON con file_url, bucket, content_type, size.

GET /images: listar imágenes con metadatos.

Extraer metadatos desde MinIO.

GET /images/{filename}: obtener URL firmada que expira (ej: 10 min).

POST /resize/{filename}: redimensionar una imagen.

Acepta width y height como parámetros.

El procesamiento se hace en background con Celery o RQ.

El job genera una nueva imagen redimensionada y la guarda en MinIO.

Devuelve un task_id y luego un endpoint para consultar el estado del job.

DELETE /images/{filename}: borrar imagen de MinIO.

Arquitectura:

FastAPI para la API.

MinIO client (boto3 o minio-py) para storage.

Celery + Redis como sistema de colas.

Pydantic para validación de modelos.

Manejo de errores robusto (archivos inexistentes, formatos inválidos, errores en la cola).

Configuración por variables de entorno (endpoint MinIO, credenciales, bucket).

Incluir un archivo docker-compose.yml que levante:

API (uvicorn)

MinIO

Redis

Worker de Celery

Entregables:

Código organizado en módulos (routes/, tasks/, config/).

requirements.txt con todas las dependencias.

Ejemplo de .env con credenciales ficticias.

Objetivo: contar con un microservicio de imágenes intermedio, seguro y escalable, con procesamiento asíncrono y almacenamiento externo.