from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page, paginate

from data import *

router = APIRouter(prefix="/games")


@router.get("/")
async def get_games(player_id: Optional[str] = None) -> Page[resp.Game]:
    """Get all games"""
    if player_id is not None:
        return paginate(
            await mdl.Game.find(
                Or(
                    In(player_id, mdl.Game.team_a.players or []),
                    In(player_id, mdl.Game.team_b.players or []),
                ),
                projection_model=resp.Game,
                fetch_links=True,
            ).to_list()
        )
    return paginate(
        await mdl.Game.find(projection_model=resp.Game, fetch_links=True).to_list()
    )


@router.post("/")
async def new_game(game: req.Game) -> resp.Status:
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
    if mdl.Team.get(game.team_a) is None:
        raise HTTPException(status_code=404, detail="Team A not found")
    if mdl.Team.get(game.team_b) is None:
        raise HTTPException(status_code=404, detail="Team B not found")
    new_game = mdl.Game(
        name=game.name,
        description=game.description,
        from_datetime=game.from_datetime,
        to_datetime=game.to_datetime,
        team_a=game.team_a,
        team_b=game.team_b,
    )
    await new_game.save()
    return resp.Status(status="ok")


@router.get("/{game_id}")
async def get_game(game_id: str) -> resp.Game:
    """Get game by id"""
    return await mdl.Game.get(game_id, projection_model=resp.Game, fetch_links=True)
