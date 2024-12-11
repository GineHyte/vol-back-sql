from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session

from app.data.models import *
from app.core.db import engine

router = APIRouter()

@router.get("/")
async def get_games(player_id: Optional[str] = None) -> Page[Game]:
    """Get all games"""
    with Session(engine) as session:
        if player_id is not None:
            statement = select(Game).where(Game.id == player_id)
            return paginate(session.exec(statement).fetchall())
        statement = select(Game)
        return paginate(session.exec(select(Game)).fetchall())


@router.post("/")
async def new_game(game: Game) -> Status:
    """Create new game"""
    if game.team_a == game.team_b:
        raise HTTPException(
            status_code=400, detail="Team A and Team B should be different"
        )
    if game.from_datetime is not None and game.to_datetime is not None:
        if game.from_datetime >= game.to_datetime:
            raise HTTPException(
                status_code=400, detail="From datetime should be less than to datetime"
            )

    with Session(engine) as session:
        statement = select(Team).where(Team.id == game.team_a)
        if session.exec(statement).first() is None:
            raise HTTPException(status_code=404, detail="Team A not found")
        if session.exec(statement).first() is None:
            raise HTTPException(status_code=404, detail="Team B not found")
        new_game = Game(
            name=game.name,
            description=game.description,
            from_datetime=game.from_datetime,
            to_datetime=game.to_datetime,
            team_a=game.team_a,
            team_b=game.team_b,
        )
        await session.add(new_game)
        await session.commit()
        return Status(status="ok")


@router.get("/{game_id}")
async def get_game(game_id: str) -> Game:
    """Get game by id"""
    with Session(engine) as session:
        statement = select(Game).where(Game.id == game_id)
        game = session.exec(statement).first()
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        return game
