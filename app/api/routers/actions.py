from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session, delete, col

from app.core.db import engine, get_session
from app.data.db import Team, Game, Action, Player, Subtech, Tech
from app.data.utils import Status
from app.data.update import ActionUpdate
from app.data.create import ActionCreate
from app.data.public import ActionPublic
from app.core.logger import logger


router = APIRouter()


@router.get("/", response_model=Page[ActionPublic])
async def get_actions(
    *, session: Session = Depends(get_session), game_id: int
) -> Page[ActionPublic]:
    """Get all actions for a game"""
    if game_id:
        return paginate(
            session.exec(select(Action).where(col(Action.game) == game_id)).all()
        )
    else:
        return paginate(session.exec(select(Action)).all())


@router.get("/{action_id}")
async def get_action(
    *, session: Session = Depends(get_session), action_id: str
) -> Action:
    """Get action by id"""
    db_action = session.get(Action, action_id)
    if not db_action:
        raise HTTPException(status_code=404, detail="Action not found")
    return db_action


@router.post("/", response_model=Status)
async def create_action(
    *, session: Session = Depends(get_session), new_action: ActionCreate
) -> Status:
    """Create new action"""
    action = Action(**new_action.model_dump())

    session.add(action)
    session.commit()

    return Status(status="success", detail="Action created")


@router.delete("/{action_id}")
async def delete_action(
    *, session: Session = Depends(get_session), action_id: str
) -> Status:
    """Delete action by id"""
    action = session.get(Action, action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")
    session.delete(action)
    session.commit()
    return Status(status="success", detail="Action deleted")


@router.put("/{action_id}")
async def update_action(
    *, session: Session = Depends(get_session), action_id: str, new_action: ActionUpdate
) -> Status:
    """Update action by id"""
    action = session.get(Action, action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")

    for field, value in new_action.model_dump(exclude_none=True).items():
        setattr(action, field, value)

    session.add(action)
    session.commit()

    return Status(status="success", detail="Action updated")
