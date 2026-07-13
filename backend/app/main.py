"""
MedVisionAI — FastAPI Application Entry Point
Phase 6: Final Integration & Polish.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
import os

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .core.config import get_settings
from .core.database import engine, Base, SessionLocal
from .models import models as _models  # noqa: F401 — registers ORM tables
from .routers import auth_router, predict_router, history_router

logger = logging.getLogger(__name__)
settings = get_settings()

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── Body size guard middleware ────────────────────────────────────
MAX_BODY_BYTES = 11 * 1024 * 1024  # 11 MB hard cap


class ContentSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds the cap."""

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_BYTES:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": f"Request body too large. Maximum is {MAX_BODY_BYTES // (1024*1024)} MB."},
            )
        return await call_next(request)


# ── Lifespan ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables and ensure upload dir exists on startup."""
    Base.metadata.create_all(bind=engine)
    logger.info("MedVisionAI backend started — DB tables ensured.")
    yield
    logger.info("MedVisionAI backend shutting down.")


# ── App factory ───────────────────────────────────────────────────
app = FastAPI(
    title="MedVisionAI API",
    description=(
        "Medical Image Analysis Platform — "
        "Chest X-ray Classification with Grad-CAM Explainability.\n\n"
        "**Auth:** Register → Login → get Bearer token → use on protected routes."
    ),
    version="6.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middlewares ───────────────────────────────────────────────────
app.add_middleware(ContentSizeLimitMiddleware)

origins = [o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler — no raw stack traces to the client ─
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# ── Static file serving (uploaded images) ────────────────────────
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# ── Routers ──────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(history_router)


# ── System Endpoints ─────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check():
    """Returns service liveness + DB connectivity status."""
    db_status = "ok"
    try:
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
    except Exception as exc:
        logger.warning(f"Health check — DB unreachable: {exc}")
        db_status = "unreachable"

    return {
        "status": "ok",
        "db": db_status,
        "service": "MedVisionAI Backend",
        "version": "6.0.0",
        "endpoints": ["/api/auth/register", "/api/auth/login", "/api/predict", "/api/history"],
    }


@app.get("/", tags=["System"])
def root():
    return {"message": "MedVisionAI API — visit /docs for interactive Swagger UI."}
