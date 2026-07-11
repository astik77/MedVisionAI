"""
MedVisionAI — History Router
================================
GET /api/history  — Paginated list of the current user's past predictions
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import User, PredictionHistory
from ..schemas.schemas import PredictionHistoryResponse, PredictionHistoryItem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/history", tags=["History"])


@router.get(
    "",
    response_model=PredictionHistoryResponse,
    summary="Get the authenticated user's scan history",
)
def get_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns a paginated list of past predictions for the logged-in user,
    ordered by most-recent first.

    - **page**: 1-indexed page number
    - **page_size**: number of records per page (max 100)
    """
    base_query = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == current_user.id)
        .order_by(desc(PredictionHistory.timestamp))
    )

    total = base_query.count()
    offset = (page - 1) * page_size
    records = base_query.offset(offset).limit(page_size).all()

    items = [
        PredictionHistoryItem(
            id=r.id,
            prediction_result=r.prediction_result,
            confidence_score=r.confidence_score,
            image_path=r.image_path,
            gradcam_path=r.gradcam_path,
            all_predictions=r.all_predictions,
            timestamp=r.timestamp,
        )
        for r in records
    ]

    return PredictionHistoryResponse(total=total, items=items)


@router.delete(
    "/{prediction_id}",
    status_code=204,
    summary="Delete a prediction record",
)
def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete one of the user's own prediction records."""
    record = (
        db.query(PredictionHistory)
        .filter(
            PredictionHistory.id == prediction_id,
            PredictionHistory.user_id == current_user.id,
        )
        .first()
    )
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prediction record not found.")

    db.delete(record)
    db.commit()
