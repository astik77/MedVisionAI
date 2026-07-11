"""
MedVisionAI — FastAPI Application Entry Point
Phase 1 stub: health check only.
Full routes (auth, predict, history) added in subsequent phases.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="MedVisionAI API",
    description="Medical Image Analysis Platform — Chest X-ray Classification with Grad-CAM",
    version="1.0.0",
)

# ── CORS ────────────────────────────────────────────────────
origins = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "MedVisionAI Backend"}


# ── Root ─────────────────────────────────────────────────────
@app.get("/", tags=["System"])
def root():
    return {"message": "Welcome to MedVisionAI API. Visit /docs for Swagger UI."}
