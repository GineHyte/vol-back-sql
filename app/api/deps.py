from hashlib import sha256
from typing import Dict, Any

import jwt 
from sqlmodel import select, Session, col, SQLModel, desc, delete, and_, func
from fastapi import HTTPException

from app.data.db import Coach
from app.data.create import AuthCreate
from app.core.config import settings

ParkedDomainPage = CustomizedPage[
    Page[T],
    UseName("ParkedDomainPage"),
    UseParamsFields(
        size=Query(
            le=500,
            alias="per_page",
        ),
    ),
    UseFieldsAliases(
        items="parked_domains",
        size="per_page",
    ),
    UseExcludedFields("total"),
]



def get_coach(session: Session, auth: AuthCreate) -> Coach:
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