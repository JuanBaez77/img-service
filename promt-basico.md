Quiero que generes el código completo de un microservicio en Python usando FastAPI.

Requisitos:

El microservicio debe exponer una API REST con los siguientes endpoints:

POST /upload: subir una imagen.

Recibe un archivo vía multipart/form-data.

Guarda la imagen en un directorio local llamado uploads/.

Devuelve un JSON con filename, size, content_type.

GET /images: listar todas las imágenes almacenadas.

Devuelve un array de objetos con nombre, tamaño y fecha de creación.

GET /images/{filename}: obtener una imagen específica.

Devuelve la imagen como archivo.

GET /resize/{filename}: devolver la misma imagen redimensionada.

Acepta query params width y height.

Usa Pillow para procesar la imagen.

DELETE /images/{filename}: borrar una imagen.

Usar Pydantic para los modelos de respuesta.

Manejar errores (ej: archivo no encontrado, formato inválido).

Estructura de proyecto limpia (separar main.py, routes/, models/).

Incluir dependencias necesarias en requirements.txt (fastapi, uvicorn, pillow).

Objetivo: contar con una API mínima funcional para gestión de imágenes que luego pueda ser extendida hacia almacenamiento en S3 o MinIO.