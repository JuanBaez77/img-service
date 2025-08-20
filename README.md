# API de Gestión de Imágenes

Microservicio en Python usando FastAPI para la gestión de imágenes con almacenamiento local.

## Características

- ✅ Subir imágenes (POST /upload)
- ✅ Listar imágenes (GET /images)
- ✅ Obtener imagen específica (GET /images/{filename})
- ✅ Redimensionar imágenes (GET /resize/{filename})
- ✅ Eliminar imágenes (DELETE /images/{filename})
- ✅ Validación de formatos de imagen
- ✅ Manejo de errores robusto
- ✅ Documentación automática con Swagger UI

## Instalación

1. **Clonar el repositorio:**
```bash
git clone <tu-repositorio>
cd api-assets
```

2. **Crear entorno virtual:**
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar el servidor:
```bash
python main.py
```

O alternativamente:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Acceder a la documentación:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

### POST /api/v1/upload
Subir una imagen. Acepta archivos multipart/form-data.

**Respuesta:**
```json
{
  "filename": "imagen_20231201_143022.jpg",
  "size": 1024000,
  "content_type": "image/jpeg"
}
```

### GET /api/v1/images
Listar todas las imágenes almacenadas.

**Respuesta:**
```json
{
  "images": [
    {
      "nombre": "imagen_20231201_143022.jpg",
      "tamaño": 1024000,
      "fecha_creacion": "2023-12-01T14:30:22"
    }
  ]
}
```

### GET /api/v1/images/{filename}
Obtener una imagen específica.

### GET /api/v1/resize/{filename}?width=X&height=Y
Redimensionar una imagen. Requiere parámetros `width` y `height`.

### DELETE /api/v1/images/{filename}
Eliminar una imagen específica.

## Formatos de imagen soportados

- JPG/JPEG
- PNG
- GIF
- BMP
- WebP

## Estructura del proyecto

```
api-assets/
├── main.py              # Aplicación principal
├── models.py            # Modelos Pydantic
├── requirements.txt     # Dependencias
├── README.md           # Este archivo
├── routes/
│   ├── __init__.py     # Inicializador del paquete
│   └── images.py       # Endpoints de imágenes
└── uploads/            # Directorio de almacenamiento (se crea automáticamente)
```

## Desarrollo

### Agregar nuevas funcionalidades:
1. Crear nuevos endpoints en `routes/images.py`
2. Agregar modelos en `models.py` si es necesario
3. Actualizar la documentación

### Extensión futura:
El microservicio está diseñado para ser fácilmente extensible hacia:
- Almacenamiento en S3
- Almacenamiento en MinIO
- Base de datos para metadatos
- Cache con Redis
- Procesamiento asíncrono de imágenes

## Licencia

MIT
