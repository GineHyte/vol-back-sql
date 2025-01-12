from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session, delete, col

from app.core.db import engine, get_session
from app.data.db import Team, Player, TeamToPlayer
from app.data.utils import Status
from app.data.update import TeamUpdate
from app.data.create import TeamCreate
from app.data.public import TeamPublic, TeamToPlayerPublic
from app.core.logger import logger


router = APIRouter()


@router.get("/", response_model=Page[TeamPublic])
async def get_teams(*, session: Session = Depends(get_session)) -> Page[TeamPublic]:
    """Get all teams"""
    db_teams = session.exec(select(Team)).all()

    return paginate(db_teams)


@router.get("/{team_id}", response_model=TeamPublic)
async def get_team(
    *, session: Session = Depends(get_session), team_id: str
) -> TeamPublic:
    """Get team by id"""
    db_team = session.get(Team, team_id)
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")

    return db_team


@router.post("/", response_model=Status)
async def new_team(
    *, session: Session = Depends(get_session), team: TeamCreate
) -> Status:
    """Create new team"""
    new_team = Team(**team.model_dump(exclude={"players"}))
    # get new id
    new_id = (
        session.exec(select(col(Team.id)).order_by(Team.id.desc())).first() or 0
    ) + 1
    logger.debug("creating new team with id %s", new_id)
    player_ids = list(map(lambda x: x.player_id, team.players))
    player_ampluas = list(map(lambda x: x.amplua, team.players))
    statement = select(Player).where(Player.id.in_(player_ids))
    players: List[Player] = session.exec(statement).all()

    if len(players) != len(player_ids) or None in players:
        raise HTTPException(status_code=404, detail="Player not found")

    for player, amplua in zip(players, player_ampluas):
        relation = TeamToPlayer(team_id=new_id, player_id=player.id, amplua=amplua)
        session.add(relation)
    session.add(new_team)
    session.commit()
    return Status(status="success", detail="Team created")


@router.delete("/{team_id}")
async def delete_team(
    *, session: Session = Depends(get_session), team_id: str
) -> Status:
    """Delete team by id"""
    team = session.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    session.delete(team)
    session.commit()
    return Status(status="success", detail="Team deleted")


@router.put("/{team_id}", response_model=Status)
async def update_team(
    *, session: Session = Depends(get_session), team_id: str, new_team: TeamUpdate
) -> Status:
    """Update team by id"""
    team = session.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    new_team_data = new_team.model_dump(exclude={"players"})
    new_team_data["players"] = []

    for player in new_team.players:
        new_team_data["players"].append(session.get(Player, player.player_id))

    team.sqlmodel_update(new_team_data)

    session.add(team)
    session.commit()

    return Status(status="success", detail="Team updated")
