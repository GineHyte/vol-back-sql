import secrets
from typing import List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select, Session, delete, col

from app.core.db import get_session
from app.data.create import AuthCreate, TokenCreate
from app.data.db import Coach, CoachSession
from app.data.public import CoachSessionPublic
from app.api.deps import get_coach, create_jwt
from app.core.config import settings

router = APIRouter()


@router.post("/login")
def post_login(*, session: Session = Depends(get_session), auth: AuthCreate):
    """Sends both access and refresh token to the user."""
    coach = get_coach(session, auth)

    refresh_token = create_jwt({"username": auth.username, "password": auth.password})
    access_token = create_jwt(
        {"refresh_token": refresh_token, "timestamp": datetime.timestamp()}
    )
    coach_session = CoachSession(
        coach=coach.id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime.now()
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    session.add(coach_session)
    session.commit()

    coach_session_public = CoachSessionPublic(
        **coach_session.model_dump(exclude=["expires_at", "coach"])
    )
    coach_session_public.expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return coach_session_public


@router.post("/token")
def post_token(*, session: Session = Depends(get_session), token: TokenCreate):
    """"""
    coach_session = session.get(CoachSession, token.refresh_token)
    if not coach_session:
        raise HTTPException("401", "Unauthoritized")

    if session.get(Coach, coach_session.coach).username != token.username:
        raise HTTPException("401", "Unauthoritized")

    if datetime.now() > coach_session.expires_at:
        raise HTTPException("401", "Token expired")

    coach_session = CoachSessionPublic(
        access_token=create_jwt(
            {"refresh_token": token.refresh_token, "timestamp": datetime.timestamp()}
        ),
        refresh_token=token.refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return coach_session
