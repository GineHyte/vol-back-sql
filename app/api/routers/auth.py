from hashlib import sha256
from typing import List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select, Session, delete, col

from app.core.db import get_session
from app.data.create import AuthCreate, TokenCreate, CoachCreate
from app.data.db import Coach, CoachSession
from app.data.public import CoachSessionPublic
from app.api.deps import auth_coach, create_jwt
from app.core.config import settings
from app.core.logger import logger

router = APIRouter()


@router.post("/login")
def post_login(*, session: Session = Depends(get_session), auth: AuthCreate):
    """Sends both access and refresh token to the user."""
    coach = auth_coach(session, auth)

    refresh_token = create_jwt({"username": auth.username, "password": auth.password})
    access_token = create_jwt(
        {"refresh_token": refresh_token, "timestamp": int(datetime.now().timestamp())}
    )

    coach_session = session.get(CoachSession, refresh_token)
    if not coach_session:
        coach_session = CoachSession(
            coach=coach.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=int(datetime.now().timestamp()) + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        session.add(coach_session)
        session.commit()
        session.refresh(coach_session)
    else:
        coach_session.access_token = access_token
        coach_session.expires_at = int(datetime.now().timestamp()) + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    coach_session_public = CoachSessionPublic(
        **coach_session.model_dump(exclude=["expires_at", "coach"]),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return coach_session_public


@router.post("/token")
def post_token(*, session: Session = Depends(get_session), token: TokenCreate):
    """"""
    coach_session = session.get(CoachSession, token.refresh_token)
    if not coach_session:
        raise HTTPException(401, "Unauthoritized")

    if session.get(Coach, coach_session.coach).username != token.username:
        raise HTTPException(401, "Unauthoritized")

    if datetime.now() > coach_session.expires_at:
        raise HTTPException(401, "Token expired")

    coach_session = CoachSessionPublic(
        access_token=create_jwt(
            {"refresh_token": token.refresh_token, "timestamp": datetime.now().timestamp()}
        ),
        refresh_token=token.refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return coach_session


@router.post("/register")
def post_register(*, session: Session = Depends(get_session), new_coach: CoachCreate):
    """Registers a new coach and returns a session."""
    if session.exec(select(Coach).where(col(Coach.username) == new_coach.username)).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    coach = Coach(
        **new_coach.model_dump(exclude={"password"}),
        password=sha256(new_coach.password.encode()).hexdigest()
    )
    session.add(coach)
    session.commit()
    session.refresh(coach)

    return post_login(session=session, auth=coach)
