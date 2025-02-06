from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session

from app.core.db import get_session
from app.data.db import Subtech
from app.data.utils import Status
from app.data.update import SubtechUpdate
from app.data.create import SubtechCreate
from app.data.public import SubtechPublic
from app.data.utils import NameWithId
from app.core.logger import logger

router = APIRouter()


@router.get("/", response_model=Page[SubtechPublic])
async def get_subtechs(
    *, session: Session = Depends(get_session), tech_id: Optional[str] = None
) -> Page[SubtechPublic]:
    """Get all subtechs"""
    if tech_id:
        db_subtechs = session.exec(select(Subtech).where(Subtech.tech == tech_id)).all()
    else:
        db_subtechs = session.exec(select(Subtech)).all()
    subtechs = []
    for db_subtech in db_subtechs:
        logger.debug(f"DB Subtech: {db_subtech}")
        subtech = SubtechPublic(**db_subtech.model_dump(exclude={"tech"}))
        subtech.tech = NameWithId(
            id=db_subtech.tech, name=session.get(Subtech, db_subtech.tech).name
        )
        subtechs.append(subtech)

    logger.info(f"Subtechs: {subtechs}")
    return paginate(subtechs)


@router.get("/{subtech_id}")
async def get_subtech(
    *, session: Session = Depends(get_session), subtech_id: str
) -> SubtechPublic:
    """Get subtech by id"""
    db_subtech = session.get(Subtech, subtech_id)
    if not db_subtech:
        raise HTTPException(status_code=404, detail="Subtech not found")

    subtech = SubtechPublic(**db_subtech.model_dump(exclude={"tech"}))
    subtech.tech = NameWithId(
        id=db_subtech.tech, name=session.get(Subtech, db_subtech.tech).name
    )
    return subtech


@router.post("/", response_model=Status)
async def create_subtech(
    *, session: Session = Depends(get_session), new_subtech: SubtechCreate
) -> Status:
    """Create new subtech"""
    subtech = Subtech(**new_subtech.model_dump())
    session.add(subtech)
    session.commit()
    return Status(status="success", detail="Subtech created")


@router.delete("/{subtech_id}")
async def delete_subtech(
    *, session: Session = Depends(get_session), subtech_id: str
) -> Status:
    """Delete subtech by id"""
    subtech = session.get(Subtech, subtech_id)
    if subtech is None:
        raise HTTPException(status_code=404, detail="Subtech not found")
    session.delete(subtech)
    session.commit()
    return Status(status="success", detail="Subtech deleted")


@router.put("/{tech_id}")
async def update_subtech(
    *,
    session: Session = Depends(get_session),
    subtech_id: str,
    new_subtech: SubtechUpdate
) -> Status:
    """Update subtech by id"""
    subtech = session.get(Subtech, subtech_id)
    if subtech is None:
        raise HTTPException(status_code=404, detail="Subtech not found")

    for field, value in new_subtech.model_dump(exclude_none=True).items():
        setattr(subtech, field, value)

    session.add(subtech)
    session.commit()

    return Status(status="success", detail="Subtech updated")
