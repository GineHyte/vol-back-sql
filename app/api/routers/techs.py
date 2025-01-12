from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session, delete, col

from app.core.db import engine, get_session
from app.data.db import Team, Game, Tech, Player, Subtech, Action
from app.data.utils import Status
from app.data.update import TechUpdate
from app.data.create import TechCreate
from app.data.public import TechPublic
from app.core.logger import logger


router = APIRouter()


@router.get("/", response_model=Page[TechPublic])
async def get_techs(*, session: Session = Depends(get_session)) -> Page[TechPublic]:
    """Get all techs"""
    return paginate(session.exec(select(Tech)).all())


@router.get("/{tech_id}")
async def get_tech(*, session: Session = Depends(get_session), tech_id: str) -> Tech:
    """Get tech by id"""
    db_tech = session.get(Tech, tech_id)
    if not db_tech:
        raise HTTPException(status_code=404, detail="Tech not found")
    return db_tech


@router.post("/", response_model=Status)
async def create_tech(
    *, session: Session = Depends(get_session), new_tech: TechCreate
) -> Status:
    """Create new tech"""
    tech = Tech(**new_tech.model_dump(exclude={"team", "player", "subtech"}))
    session.add(tech)
    session.commit()
    return Status(status="success", detail="Tech created")


@router.delete("/{tech_id}")
async def delete_tech(
    *, session: Session = Depends(get_session), tech_id: str
) -> Status:
    """Delete tech by id"""
    tech = session.get(Tech, tech_id)
    if tech is None:
        raise HTTPException(status_code=404, detail="Tech not found")
    session.delete(tech)
    session.commit()
    return Status(status="success", detail="Tech deleted")


@router.put("/{tech_id}")
async def update_tech(
    *, session: Session = Depends(get_session), tech_id: str, new_tech: TechUpdate
) -> Status:
    """Update tech by id"""
    tech = session.get(Tech, tech_id)
    if tech is None:
        raise HTTPException(status_code=404, detail="Tech not found")

    for field, value in new_tech.model_dump(exclude_none=True).items():
        setattr(tech, field, value)

    session.add(tech)
    session.commit()

    return Status(status="success", detail="Tech updated")
