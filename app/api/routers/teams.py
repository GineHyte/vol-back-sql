from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException
from bson import ObjectId

from data import *

router = APIRouter(prefix="/teams")


@router.get("/")
async def get_teams() -> List[resp.Team]:
    """Get all teams"""
    return await mdl.Team.find(projection_model=resp.Team, fetch_links=True).to_list()


@router.get("/{team_id}")
async def get_team(team_id: str) -> resp.Team:
    """Get team by id"""
    return await mdl.Team.get(team_id, projection_model=resp.Team, fetch_links=True)


@router.post("/")
async def new_team(team: req.Team) -> resp.Status:
    """Create new team"""
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
