from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page, paginate
from beanie import PydanticObjectId

from data import *

router = APIRouter(prefix="/players")


@router.get("/")
async def get_players() -> Page[resp.Player]:
    """Get all players"""
    return paginate(await mdl.Player.find(projection_model=resp.Player).to_list())


@router.get("/{player_id}")
async def get_player(player_id: str) -> resp.Player:
    """Get player by id"""
    return await mdl.Player.get(
        player_id, projection_model=resp.Player, fetch_links=True
    )


@router.post("/")
async def new_player(player: req.Player) -> resp.Status:
    """Create new player"""
    new_player = mdl.Player(
        first_name=player.first_name,
        last_name=player.last_name,
        age=player.age,
        height=player.height,
        weight=player.weight,
        amplua=player.amplua,
    )
    await new_player.save()
    return resp.Status(status="ok")


# @router.get("/{player_id}")
# async def get_player(player_id: str) -> Dict[str, Any]:
#     return (await mdl.Player.find_one(mdl.Player.id == player_id)).model_dump()


# @router.delete("/{player_id}")
# async def delete_player(player_id: str) -> Dict[str, Any]:
#     player = await mdl.Player.find_one(mdl.Player.id == ObjectId(player_id))
#     if not player:
#         raise HTTPException(status_code=404, detail="Player not found")
#     await player.delete()
#     return player.model_dump()


# @router.put("/{player_id}")
# async def update_player(player_id: str, player: NewPlayer) -> Dict[str, Any]:
#     player_old = await mdl.Player.find_one(mdl.Player.id == ObjectId(player_id))
#     if not player_old:
#         raise HTTPException(status_code=404, detail="Player not found")

#     player = await player_old.set(player.model_dump())

#     return player.model_dump()
