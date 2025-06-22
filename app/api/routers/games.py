from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session, delete, col, or_

from app.core.db import engine, get_session
from app.data.db import Team, Game, Player, Action
from app.data.utils import Status, NameWithId
from app.data.update import GameUpdate
from app.data.create import GameCreate
from app.data.public import GamePublic
from app.core.logger import logger


router = APIRouter()


@router.get("/", response_model=Page[GamePublic])
async def get_games(
    *,
    session: Session = Depends(get_session),
    player_id: int = None,
    team_id: int = None,
) -> Page[GamePublic]:
    """Get all games

    :param player_id: When provided, returns games where player is in team
    :param team_id: When provided, returns games where team is playing

    :return: List of games (if nether player_id nor team_id provided, returns all games)
    """
    games = []
    if player_id:
        db_games = []
        db_games_ids = set()
        player = session.get(Player, player_id)
        for team_to_player in player.teams:
            t_games = session.exec(
                select(Game).where(
                    or_(
                        Game.team_a == team_to_player.team_id,
                        Game.team_b == team_to_player.team_id,
                    )
                )
            ).all()
            for t_game in t_games:
                if t_game.id not in db_games_ids:
                    db_games_ids.add(t_game.id)
                    db_games.append(t_game)
    elif team_id:
        db_games = session.exec(
            select(Game).where(or_(Game.team_a == team_id, Game.team_b == team_id))
        ).all()
    else:
        db_games = session.exec(select(Game)).all()
    for db_game in db_games:
        game = GamePublic(**db_game.model_dump(exclude={"team_a", "team_b"}))
        team_a = session.get(Team, db_game.team_a)
        if team_a:
            game.team_a = NameWithId(id=db_game.team_a, name=team_a.name)
        team_b = session.get(Team, db_game.team_b)
        if team_b:
            game.team_b = NameWithId(id=db_game.team_b, name=team_b.name)
        games.append(game)
    return paginate(games)


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

    if game.from_timestamp and game.to_timestamp:
        if game.from_timestamp > game.to_timestamp:
            raise HTTPException(status_code=400, detail="Incorrect timestamp")

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
    
    # Delete related actions
    session.exec(delete(Action).where(Action.game == game_id))
    session.commit()
    
    # Delete the game
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


@router.get("/clone/{game_id}")
async def deep_clone_game(
    *, session: Session = Depends(get_session), game_id: str
) -> Status:
    """Deep clone game"""
    game = session.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    game_clone = game.model_dump(exclude={"id"})
    new_game = Game(**game_clone)

    session.add(new_game)
    session.commit()
    session.refresh(new_game)
    logger.debug(f"Cloning game {game_id} with data: {new_game}")

    for action in session.exec(select(Action).where(Action.game == game_id)).all(): 
        action_clone = action.model_dump(exclude={"id", "game"})
        action_clone["game"] = new_game.id
        new_action = Action(**action_clone)
        session.add(new_action)

    session.commit()

    return Status(status="success", detail="Game cloned successfully")
