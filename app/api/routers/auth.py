from typing import List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select, Session, delete, col

from app.core.db import get_session
from app.data.create import AuthCreate
from app.data.db import Coach, CoachSession
from app.data.public import CoachSessionPublic
from app.api.deps import get_coach, create_jwt
from app.core.config import settings

router = APIRouter()

@router.post("/login")
def get_token(
    *, session: Session = Depends(get_session), auth: AuthCreate
):
    """Sends both access and refresh token to the user."""
    coach = get_coach(session, auth)

    coach_session = CoachSession(
        coach=coach.id,
        refresh_token=create_jwt(auth),
        expires_at=datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

