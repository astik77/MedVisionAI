"""
MedVisionAI — Application Configuration
Reads all settings from environment variables (or .env file via python-dotenv).
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./medvision.db"

    # ── JWT ──────────────────────────────────────────────────
    SECRET_KEY: str = "change_me_to_a_long_random_string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── CORS ─────────────────────────────────────────────────
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173"

    # ── App ──────────────────────────────────────────────────
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
