from hashlib import sha256
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select, Session, delete, col

from app.core.db import get_session
from app.data.create import AuthCreate, TokenCreate, CoachCreate
from app.data.db import Coach, CoachSession
from app.data.public import CoachSessionPublic
from app.api.deps import auth_coach, create_jwt
from app.core.config import settings

router = APIRouter()


@router.post("/login")
def post_login(*, session: Session = Depends(get_session), auth: AuthCreate):
    """
    Authenticates a coach and returns both access and refresh tokens.
    
    Args:
        session: Database session dependency
        auth: Authentication credentials containing username and password
        
    Returns:
        CoachSessionPublic: Session data with access token, refresh token, and expiration info
        
    Raises:
        HTTPException: If authentication fails (handled by auth_coach dependency)
    """
    # Authenticate the coach using provided credentials
    coach = auth_coach(session, auth)

    # Generate refresh token containing username and password for persistence
    refresh_token = create_jwt({"username": auth.username, "password": auth.password})
    
    # Generate access token containing refresh token reference and current timestamp
    access_token = create_jwt(
        {"refresh_token": refresh_token, "timestamp": int(datetime.now().timestamp())}
    )

    # Check if a session already exists for this refresh token
    coach_session = session.get(CoachSession, refresh_token)
    if not coach_session:
        # Create new session record if none exists
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
        # Update existing session with new access token and expiration
        coach_session.access_token = access_token
        coach_session.expires_at = int(datetime.now().timestamp()) + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # Create public response object excluding sensitive fields
    coach_session_public = CoachSessionPublic(
        **coach_session.model_dump(exclude=["expires_at", "coach"]),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return coach_session_public


@router.post("/token")
def post_token(*, session: Session = Depends(get_session), token: TokenCreate):
    """
    Refreshes an access token using a valid refresh token.
    
    Args:
        session: Database session dependency
        token: Token refresh request containing refresh token and username
        
    Returns:
        CoachSessionPublic: New session data with refreshed access token
        
    Raises:
        HTTPException: 401 if token is invalid, expired, or username doesn't match
    """
    # Retrieve the existing coach session using the refresh token
    coach_session = session.get(CoachSession, token.refresh_token)
    if not coach_session:
        raise HTTPException(401, "Unauthorized")

    # Verify that the username matches the session owner
    if session.get(Coach, coach_session.coach).username != token.username:
        raise HTTPException(401, "Unauthorized")

    # Check if the session has expired
    if datetime.now() > coach_session.expires_at:
        raise HTTPException(401, "Token expired")

    # Create new session data with refreshed access token
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
    """
    Registers a new coach and returns a session.
    
    Args:
        session: Database session dependency
        new_coach: Complete coach registration data including username and password
        
    Returns:
        CoachSessionPublic: Session data for the newly registered coach
        
    Raises:
        HTTPException: 400 if username already exists
    """
    # Check if username already exists in the database
    if session.exec(select(Coach).where(col(Coach.username) == new_coach.username)).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create new coach record with hashed password
    coach = Coach(
        **new_coach.model_dump(exclude={"password"}),
        password=sha256(new_coach.password.encode()).hexdigest()
    )
    session.add(coach)
    session.commit()
    session.refresh(coach)

    # Automatically log in the newly registered coach
    return post_login(session=session, auth=coach)
