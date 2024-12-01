from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session

from app.data.models import *
from app.core.db import engine

router = APIRouter(prefix="/teams")


@router.get("/")
async def get_teams() -> Page[Team]:
    """Get all teams"""
    with Session(engine) as session:
        statement = select(Team)
        return paginate(session.exec(statement).fetchall())


@router.get("/{team_id}")
async def get_team(team_id: str) -> Team:
    """Get team by id"""
    with Session(engine) as session:
        statement = select(Team).where(Team.id == team_id)
        team = session.exec(statement).first()
        if team is None:
            raise HTTPException(status_code=404, detail="Team not found")
        return team


@router.post("/")
async def new_team(team: Team) -> Status:
    """Create new team"""
    with Session(engine) as session:
        for player_id in team.players:
            player = await mdl.Player.get(player_id)
            if not player:
                raise HTTPException(status_code=404, detail="Player not found")

        new_team = mdl.Team(
            name=team.name,
            players=team.players,
            coach=team.coach,
        )
        await new_team.save()
        return resp.Status(status="ok")


# @router.get("/{team_id}")
# async def get_team(team_id: str) -> Dict[str, Any]:
#     return (await Team.find_one(Team.id == team_id)).model_dump()

# @router.delete("/{team_id}")
# async def delete_team(team_id: str) -> Dict[str, Any]:
#     team = await Team.find_one(Team.id == ObjectId(team_id))
#     if not team:
#         raise HTTPException(status_code=404, detail="Team not found")
#     await team.delete()
#     return team.model_dump()

# @router.put("/{team_id}")
# async def update_team(team_id: str, team: NewTeam) -> Dict[str, Any]:
#     team_old = await Team.find_one(Team.id == ObjectId(team_id))
#     if not team_old:
#         raise HTTPException(status_code=404, detail="Team not found")

#     team = await team_old.set(team.model_dump())

#     return team.model_dump()
