"""
MedVisionAI — Authentication Router
Endpoints: POST /api/auth/register, POST /api/auth/login, GET /api/auth/me
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from ..core.config import get_settings
from ..models.models import User
from ..schemas.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserPublic,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
settings = get_settings()


# ── Register ─────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new MedVisionAI account.
    
    - **email**: must be unique
    - **username**: 3-50 chars, alphanumeric / _ / -
    - **password**: minimum 8 characters (stored as bcrypt hash)
    """
    # Check uniqueness
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken.",
        )

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Login ─────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT",
)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email + password.
    Returns a Bearer JWT valid for `ACCESS_TOKEN_EXPIRE_MINUTES`.
    """
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=expire_minutes),
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expire_minutes * 60,
    )


# ── Me ────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get the current authenticated user",
)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user
