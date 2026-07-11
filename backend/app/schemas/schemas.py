"""
MedVisionAI — Pydantic Schemas
Request/response models (separate from SQLAlchemy ORM models).
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth Schemas ─────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    """Payload for POST /api/auth/register"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, digits, _ or -")
        return v.lower()


class UserLoginRequest(BaseModel):
    """Payload for POST /api/auth/login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserPublic(BaseModel):
    """Safe user representation (no password hash)"""
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Prediction Schemas ───────────────────────────────────────

class PredictionResponse(BaseModel):
    """Response from POST /api/predict"""
    id: int
    prediction_result: str
    confidence_score: float
    all_predictions: Optional[str] = None
    gradcam_base64: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class PredictionHistoryItem(BaseModel):
    """Single item in prediction history list"""
    id: int
    prediction_result: str
    confidence_score: float
    image_path: str
    gradcam_path: Optional[str] = None
    all_predictions: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class PredictionHistoryResponse(BaseModel):
    """Response from GET /api/history"""
    total: int
    items: List[PredictionHistoryItem]
