"""
MedVisionAI — FastAPI Application Entry Point
Phase 4: All routers mounted.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from .core.config import get_settings
from .core.database import engine, Base
from .models import models as _models  # noqa: F401 — registers ORM tables
from .routers import auth_router, predict_router, history_router

settings = get_settings()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables and ensure upload dir exists on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="MedVisionAI API",
    description=(
        "Medical Image Analysis Platform — "
        "Chest X-ray Classification with Grad-CAM Explainability.\n\n"
        "**Auth:** Register → Login → get Bearer token → use on protected routes."
    ),
    version="4.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────
origins = [o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static file serving (uploaded images) ────────────────────
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# ── Routers ──────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(history_router)


# ── System Endpoints ─────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "service": "MedVisionAI Backend",
        "version": "4.0.0",
        "endpoints": ["/api/auth/register", "/api/auth/login", "/api/predict", "/api/history"],
    }


@app.get("/", tags=["System"])
def root():
    return {"message": "MedVisionAI API — visit /docs for interactive Swagger UI."}
