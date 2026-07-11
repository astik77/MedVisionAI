"""
MedVisionAI — SQLAlchemy ORM Models
Defines User and PredictionHistory tables.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from ..core.database import Base


class User(Base):
    """Application user — stores hashed credentials."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    predictions = relationship(
        "PredictionHistory", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class PredictionHistory(Base):
    """Stores every inference result for a user."""
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    image_path = Column(String(512), nullable=False)
    prediction_result = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)
    gradcam_path = Column(String(512), nullable=True)
    all_predictions = Column(Text, nullable=True)  # JSON string of all class scores
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    user = relationship("User", back_populates="predictions")

    def __repr__(self) -> str:
        return (
            f"<PredictionHistory id={self.id} "
            f"user_id={self.user_id} result={self.prediction_result} "
            f"confidence={self.confidence_score:.2f}>"
        )
