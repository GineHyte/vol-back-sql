from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session, delete, col

from app.core.db import engine, get_session
from app.data.db import Team, Game, Action, Player, Subtech, Tech
from app.data.utils import Status, NameWithId
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
    actions = []
    if game_id:
        db_actions = session.exec(
            select(Action).where(col(Action.game) == game_id).order_by(Action.id.desc())
        ).all()
    else:
        db_actions = session.exec(select(Action).order_by(Action.id.desc())).all()
    for db_action in db_actions:
        action = ActionPublic(
            **db_action.model_dump(exclude={"game", "team", "player", "subtech"})
        )
        action.game = NameWithId(
            id=db_action.game, name=session.get(Game, db_action.game).name
        )
        action.team = NameWithId(
            id=db_action.team, name=session.get(Team, db_action.team).name
        )
        player = session.get(Player, db_action.player)
        if player:
            action.player = NameWithId(
                id=db_action.player, name=player.first_name + " " + player.last_name
            )
        action.subtech = NameWithId(
            id=db_action.subtech, name=session.get(Subtech, db_action.subtech).name
        )
        actions.append(action)

    return paginate(actions)


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
