# API de Gestión de Imágenes - Nivel Intermedio

Microservicio en Python usando FastAPI para la gestión de imágenes con almacenamiento en MinIO, procesamiento asíncrono con Celery y cola de mensajes con Redis.

## 🚀 **Características Avanzadas**

- ✅ **Almacenamiento en MinIO** - Compatible con S3
- ✅ **Procesamiento asíncrono** - Celery + Redis para tareas en background
- ✅ **URLs firmadas** - Descarga segura con expiración configurable
- ✅ **Redimensionado asíncrono** - Procesamiento de imágenes en background
- ✅ **Metadatos de imágenes** - Información detallada de cada archivo
- ✅ **Cola de tareas** - Monitoreo y gestión de jobs
- ✅ **Configuración por variables de entorno** - Fácil despliegue
- ✅ **Docker Compose** - Infraestructura completa en un comando

## 🏗️ **Arquitectura**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   FastAPI   │    │   Celery    │    │   MinIO     │
│     API     │◄──►│   Worker    │◄──►│  Storage   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐    ┌─────────────┐
│   Redis     │    │   Flower    │
│   Queue     │    │  Monitor    │
└─────────────┘    └─────────────┘
```

## 📋 **Requisitos**

- Python 3.11+
- Docker y Docker Compose
- 4GB RAM mínimo (para toda la infraestructura)

## 🚀 **Instalación Rápida con Docker**

### **1. Clonar y configurar:**
```bash
git clone <tu-repositorio>
cd api-assets
cp env.example .env
# Editar .env si es necesario
```

### **2. Levantar toda la infraestructura:**
```bash
docker-compose up -d
```

### **3. Verificar servicios:**
- **API**: http://localhost:8000
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Flower (Celery)**: http://localhost:5555

## 🔧 **Instalación Manual**

### **1. Crear entorno virtual:**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### **2. Instalar dependencias:**
```bash
pip install -r requirements.txt
```

### **3. Configurar variables de entorno:**
```bash
cp env.example .env
# Editar .env con tus credenciales
```

### **4. Levantar servicios externos:**
```bash
# MinIO (en otra terminal)
docker run -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"

# Redis (en otra terminal)
docker run -p 6379:6379 redis:7-alpine
```

### **5. Ejecutar la aplicación:**
```bash
# Terminal 1: API
python main.py

# Terminal 2: Worker de Celery
celery -A celery_app worker --loglevel=info

# Terminal 3: Flower (opcional)
celery -A celery_app flower --port=5555
```

## 📚 **Endpoints**

### **POST /api/v1/upload**
Subir imagen a MinIO.
```json
{
  "filename": "imagen_20231201_143022.jpg",
  "bucket": "images",
  "content_type": "image/jpeg",
  "size": 1024000,
  "file_url": "minio://images/imagen_20231201_143022.jpg"
}
```

### **GET /api/v1/images**
Listar imágenes con metadatos desde MinIO.

### **GET /api/v1/images/{filename}**
Obtener URL firmada para descarga (expira en 10 min).

### **POST /api/v1/resize/{filename}**
Iniciar redimensionado asíncrono.
```json
{
  "width": 300,
  "height": 200
}
```

### **GET /api/v1/tasks/{task_id}**
Consultar estado de tarea de redimensionado.

### **DELETE /api/v1/images/{filename}**
Eliminar imagen de MinIO.

## 🔍 **Monitoreo**

### **Flower (Celery Dashboard):**
- URL: http://localhost:5555
- Monitorea tareas, workers y colas
- Estadísticas en tiempo real

### **MinIO Console:**
- URL: http://localhost:9001
- Usuario: `minioadmin`
- Contraseña: `minioadmin`
- Gestión de buckets y objetos

### **Health Checks:**
- API: http://localhost:8000/health
- Configuración: http://localhost:8000/config

## ⚙️ **Configuración**

### **Variables de Entorno (.env):**
```bash
# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=images

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Procesamiento
MAX_FILE_SIZE=10485760  # 10MB
SIGNED_URL_EXPIRY=600  # 10 min
```

## 🐳 **Docker**

### **Servicios incluidos:**
- **api**: FastAPI en puerto 8000
- **celery-worker**: Procesamiento asíncrono
- **minio**: Almacenamiento de objetos
- **redis**: Cola de mensajes
- **flower**: Monitoreo de Celery

### **Comandos útiles:**
```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Reiniciar solo la API
docker-compose restart api

# Escalar workers de Celery
docker-compose up -d --scale celery-worker=3

# Parar todos los servicios
docker-compose down
```

## 🔒 **Seguridad**

- **URLs firmadas** con expiración configurable
- **Validación de tipos** de archivo
- **Límites de tamaño** configurable
- **Autenticación MinIO** (configurable)
- **CORS configurado** para desarrollo

## 📈 **Escalabilidad**

- **Workers de Celery** escalables horizontalmente
- **Redis Cluster** para alta disponibilidad
- **MinIO Distributed** para almacenamiento distribuido
- **Load Balancer** para múltiples instancias de API

## 🚀 **Despliegue en Producción**

### **Recomendaciones:**
1. **Cambiar credenciales por defecto**
2. **Configurar HTTPS** para MinIO
3. **Usar Redis Cluster** para alta disponibilidad
4. **Configurar backup** automático de MinIO
5. **Monitoreo** con Prometheus + Grafana
6. **Logs centralizados** con ELK Stack

## 🤝 **Contribuir**

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 **Licencia**

MIT License - ver [LICENSE](LICENSE) para detalles.

## 🆘 **Soporte**

- **Issues**: GitHub Issues
- **Documentación**: `/docs` en la API
- **Health Check**: `/health` endpoint
