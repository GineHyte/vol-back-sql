from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session, delete, col

from app.core.db import engine, get_session
from app.data.db import Team, Game
from app.data.utils import Status
from app.data.update import GameUpdate
from app.data.create import GameCreate
from app.data.public import GamePublic
from app.core.logger import logger


router = APIRouter()


@router.get("/", response_model=Page[GamePublic])
async def get_games(*, session: Session = Depends(get_session)) -> Page[GamePublic]:
    """Get all games"""
    return paginate(session.exec(select(Game)).all())


@router.get("/{game_id}")
async def get_game(*, session: Session = Depends(get_session), game_id: str) -> Game:
    """Get game by id"""
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.post("/", response_model=Status)
async def create_game(
    *, session: Session = Depends(get_session), new_game: GameCreate
) -> Status:
    """Create new game"""
    game = Game(**new_game.model_dump(exclude={"team_a", "team_b"}))

    if game.from_datetime and game.to_datetime:
        if game.from_datetime > game.to_datetime:
            raise HTTPException(status_code=400, detail="Incorrect datetime")

    team_a = session.get(Team, new_game.team_a)
    team_b = session.get(Team, new_game.team_b)

    if not team_a:
        raise HTTPException(status_code=404, detail="Team A not found")

    if not team_b:
        raise HTTPException(status_code=404, detail="Team B not found")
    if team_a == team_b:
        raise HTTPException(status_code=400, detail="Teams cannot be the same")

    game.team_a = team_a.id
    game.team_b = team_b.id

    session.add(game)
    session.commit()

    return Status(status="success", detail="Game created")


@router.delete("/{game_id}")
async def delete_game(
    *, session: Session = Depends(get_session), game_id: str
) -> Status:
    """Delete game by id"""
    game = session.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    session.delete(game)
    session.commit()
    return Status(status="success", detail="Game deleted")


@router.put("/{game_id}")
async def update_game(
    *, session: Session = Depends(get_session), game_id: str, new_game: GameUpdate
) -> Status:
    """Update game by id"""
    game = session.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    for field, value in new_game.model_dump(exclude_none=True).items():
        setattr(game, field, value)

    session.add(game)
    session.commit()

    return Status(status="success", detail="Team updated")
