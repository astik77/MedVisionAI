"""
MedVisionAI — Prediction Router
=================================
POST /api/predict   — Upload an image, run ML inference, return Grad-CAM
GET  /api/predict/{id} — Retrieve one prediction record by ID
"""

import uuid
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import User, PredictionHistory
from ..schemas.schemas import PredictionResponse
from ..ml.scanner import MedicalModelScanner

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/predict", tags=["Predictions"])

# ── Upload storage ────────────────────────────────────────────
_settings = get_settings()
UPLOAD_DIR = Path(_settings.UPLOAD_DIR)

# Allowed image MIME types
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
MAX_FILE_SIZE_MB = 10

# Global scanner instance (loaded once on first predict call)
_scanner = MedicalModelScanner()


# ── POST /api/predict ─────────────────────────────────────────
@router.post(
    "",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a medical image and receive AI prediction + Grad-CAM",
)
async def predict(
    file: UploadFile = File(..., description="Medical image (JPEG / PNG / WebP / BMP)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **Protected endpoint** — requires Bearer JWT.

    Steps:
    1. Validate file type and size.
    2. Persist original image to disk.
    3. Run `MedicalModelScanner.analyse()` → prediction + Grad-CAM.
    4. Save result to `prediction_history` table.
    5. Return full `PredictionResponse` including base64 heatmap.
    """

    # ── Validate MIME type ────────────────────────────────────
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                f"Allowed: {', '.join(ALLOWED_TYPES)}"
            ),
        )

    # ── Read & validate size ──────────────────────────────────
    image_bytes = await file.read()
    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({size_mb:.1f} MB). Maximum is {MAX_FILE_SIZE_MB} MB.",
        )

    # ── Save original image ───────────────────────────────────
    ext = Path(file.filename or "upload.jpg").suffix or ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    user_upload_dir = UPLOAD_DIR / str(current_user.id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)
    image_path = user_upload_dir / unique_name

    try:
        with open(image_path, "wb") as f:
            f.write(image_bytes)
    except OSError as exc:
        logger.error(f"Failed to save upload: {exc}")
        raise HTTPException(status_code=500, detail="Could not store uploaded image.")

    # ── ML Inference + Grad-CAM ───────────────────────────────
    try:
        result = _scanner.analyse(image_bytes)
    except Exception as exc:
        logger.exception(f"ML inference failed: {exc}")
        # Clean up saved file on failure
        image_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"ML inference error: {str(exc)}")

    # ── Persist to database ───────────────────────────────────
    record = PredictionHistory(
        user_id=current_user.id,
        image_path=str(image_path.relative_to(UPLOAD_DIR)),
        prediction_result=result["prediction"],
        confidence_score=result["confidence"],
        all_predictions=result["all_scores"],
        gradcam_path=None,  # Grad-CAM returned inline (base64), not stored to disk
        timestamp=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(
        f"User {current_user.id} | id={record.id} | "
        f"{result['prediction']} ({result['confidence']:.2%})"
    )

    return PredictionResponse(
        id=record.id,
        prediction_result=record.prediction_result,
        confidence_score=record.confidence_score,
        all_predictions=record.all_predictions,
        gradcam_base64=result["gradcam_b64"],
        timestamp=record.timestamp,
    )


# ── GET /api/predict/{id} ─────────────────────────────────────
@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Retrieve a single prediction by ID",
)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch one prediction record. Users can only access their own records."""
    record = (
        db.query(PredictionHistory)
        .filter(
            PredictionHistory.id == prediction_id,
            PredictionHistory.user_id == current_user.id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Prediction not found.")

    return PredictionResponse(
        id=record.id,
        prediction_result=record.prediction_result,
        confidence_score=record.confidence_score,
        all_predictions=record.all_predictions,
        gradcam_base64=None,  # Not stored on disk; re-run predict to regenerate
        timestamp=record.timestamp,
    )
