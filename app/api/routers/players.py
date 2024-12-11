from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session

from app.core.db import engine
from app.data.models import *

router = APIRouter()

@router.get("/")
async def get_players() -> Page[Player]:
    """Get all players"""
    with Session(engine) as session:
        statement = select(Player)
        return paginate(session.exec(statement).fetchall())


@router.get("/{player_id}")
async def get_player(player_id: str) -> Player:
    """Get player by id"""
    with Session(engine) as session:
        statement = select(Player).where(Player.id == player_id)
        player = session.exec(statement).first()
        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")
        return player


@router.post("/")
async def new_player(player: Player) -> Status:
    """Create new player"""
    with Session(engine) as session:
        new_player = Player(
            first_name=player.first_name,
            last_name=player.last_name,
            age=player.age,
            height=player.height,
            weight=player.weight,
            amplua=player.amplua,
        )
        await session.add(new_player)
        await session.commit()
        return Status(status="ok")


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
