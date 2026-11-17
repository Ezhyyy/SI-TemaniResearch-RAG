import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import init_db
from app.routers import auth_router, document_router, chat_router, stats_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inisialisasi tabel database saat aplikasi mulai
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API TemaniResearch: Sistem Informasi Penelitian Berbasis AI & RAG",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware agar Frontend Next.js dapat mengakses API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Atau ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount folder upload untuk melayani akses file PDF jika dibutuhkan
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Registrasi Router
app.include_router(auth_router.router)
app.include_router(document_router.router)
app.include_router(chat_router.router)
app.include_router(stats_router.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "docs": "/docs",
        "chat_model": settings.GEMINI_CHAT_MODEL,
        "embedding_model": settings.GEMINI_EMBEDDING_MODEL
    }

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
