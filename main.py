from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import images

app = FastAPI(
    title="API de Gestión de Imágenes",
    description="Microservicio para gestión de imágenes con FastAPI",
    version="1.0.0"
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
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/v1/upload",
            "list_images": "/api/v1/images",
            "get_image": "/api/v1/images/{filename}",
            "resize_image": "/api/v1/resize/{filename}?width=X&height=Y",
            "delete_image": "/api/v1/images/{filename}"
        },
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {"status": "healthy", "service": "image-management-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
