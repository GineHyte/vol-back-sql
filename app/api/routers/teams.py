from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session, delete, col

from app.core.db import engine, get_session
from app.data.db import Team, Player, TeamToPlayer
from app.data.utils import Status
from app.data.update import TeamUpdate
from app.data.create import TeamCreate
from app.data.public import TeamPublic
from app.core.logger import logger


router = APIRouter()


@router.get("/", response_model=Page[TeamPublic])
async def get_teams(*, session: Session = Depends(get_session)) -> Page[TeamPublic]:
    """Get all teams"""
    db_teams = session.exec(select(Team)).all()
    teams = []
    for db_team in db_teams:
        players = db_team.players
        db_team.players = []
        team = TeamPublic.model_validate(db_team)
        team.players = list(map(lambda x: x.id, players))
        teams.append(team)
    logger.info(teams)
    return paginate(teams)


@router.get("/{team_id}")
async def get_team(*, session: Session = Depends(get_session), team_id: str) -> Team:
    """Get team by id"""
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


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
    player_ids = list(map(lambda x: x.player, team.players))
    player_ampluas = list(map(lambda x: x.amplua, team.players))
    statement = select(Player).where(Player.id.in_(player_ids))
    players: List[Player] = session.exec(statement).all()

    if len(players) != len(player_ids):
        raise HTTPException(status_code=404, detail="Player not found")

    for player, amplua in zip(players, player_ampluas):
        relation = TeamToPlayer(team_id=new_id, player_id=player.id, amplua=amplua)
        session.add(relation)
    session.add(new_team)
    session.commit()
    return Status(status="ok", detail="Team created")


@router.delete("/{team_id}")
async def delete_team(team_id: str) -> Status:
    """Delete team by id"""
    with Session(engine) as session:
        statement = select(Team).where(Team.id == team_id)
        team = session.exec(statement).first()
        if team is None:
            raise HTTPException(status_code=404, detail="Team not found")
        else:
            session.delete(team)
            session.commit()
        return Status(status="ok", detail="Team deleted")


@router.put("/{team_id}")
async def update_team(team_id: str, new_team: TeamUpdate) -> Status:
    """Update player by id"""
    with Session(engine) as session:
        statement = select(Team).where(Team.id == team_id)
        team = session.exec(statement).first()
        if team is None:
            raise HTTPException(status_code=404, detail="Team not found")
        else:
            for field, value in new_team.model_dump().items():
                if value is None:
                    continue
                setattr(team, field, value)
            session.add(team)
            session.commit()
            session.refresh(team)
        return Status(status="ok", detail="Team updated")
