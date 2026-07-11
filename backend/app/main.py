"""
MedVisionAI — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.database import engine, Base
from .models import models as _models  # noqa: F401 — registers ORM tables
from .routers import auth_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all DB tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="MedVisionAI API",
    description="Medical Image Analysis Platform — Chest X-ray Classification with Grad-CAM",
    version="3.0.0",
    lifespan=lifespan,
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

# ── Routers ──────────────────────────────────────────────────
app.include_router(auth_router)
# Phase 4: predict_router and history_router added here


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "MedVisionAI Backend"}


@app.get("/", tags=["System"])
def root():
    return {"message": "MedVisionAI API — visit /docs for Swagger UI."}
