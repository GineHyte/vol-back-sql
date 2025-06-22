from hashlib import sha256
from typing import Dict, Any, TypeVar
from datetime import datetime

import jwt
from sqlmodel import select, Session, col, SQLModel, delete, func, or_
from fastapi import HTTPException, Query, Request, Depends
from fastapi_pagination import Page
from fastapi_pagination.customization import CustomizedPage, UseParamsFields
from apscheduler.schedulers.background import BackgroundScheduler

from app.data.db import Coach, CoachSession
from app.data.create import AuthCreate
from app.core.config import settings
from app.core.db import get_session

T = TypeVar("T")

VolPage = CustomizedPage[
    Page[T],
    UseParamsFields(
        size=Query(100, ge=1, le=1000),
    ),
]


def get_coach(request: Request, session: Session = Depends(get_session)) -> Coach:
    """Get coach from request."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    auth_header = auth_header.replace("Bearer ", "")
    coach_session = session.exec(
        select(CoachSession).where(col(CoachSession.access_token) == auth_header)
    ).first()
    if not coach_session:
        raise HTTPException(status_code=401, detail="Invalid access token")
    coach = session.get(Coach, coach_session.coach)
    if not coach:
        raise HTTPException(status_code=401, detail="Coach not found")
    return coach


def auth_coach(session: Session, auth: AuthCreate) -> Coach:
    """Get coach by username and password."""
    coach = session.exec(
        select(Coach).where(
            col(Coach.username) == auth.username,
            col(Coach.password) == sha256(auth.password.encode()).hexdigest(),
        )
    ).first()
    if not coach:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return coach


def create_jwt(payload: Dict[str, Any]) -> str:
    """Hash password."""
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )