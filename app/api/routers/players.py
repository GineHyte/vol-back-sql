from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session, delete

from app.core.db import engine
from app.data.db import Player, PlayerCreate, PlayerUpdate, Status

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
async def new_player(player: PlayerCreate) -> Status:
    """Create new player"""
    new_player = Player(**player.model_dump())
    with Session(engine) as session:
        session.add(new_player)
        session.commit()
    return Status(status="ok")


@router.delete("/{player_id}")
async def delete_player(player_id: str) -> Status:
    """Delete player by id"""
    with Session(engine) as session:
        statement = select(Player).where(Player.id == player_id)
        player = session.exec(statement).first()
        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")
        else:
            session.delete(player)
            session.commit()
        return Status(status="ok")


@router.put("/{player_id}")
async def update_player(player_id: str, new_player: PlayerUpdate) -> Status:
    """Update player by id"""
    with Session(engine) as session:
        statement = select(Player).where(Player.id == player_id)
        player = session.exec(statement).first()
        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")
        else:
            for field, value in new_player.model_dump().items():
                if value is None: continue
                setattr(player, field, value)
            session.add(player)
            session.commit()
            session.refresh(player)
        return Status(status="ok")
