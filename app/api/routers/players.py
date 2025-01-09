from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session

from app.core.db import engine
from app.data.db import Player
from app.data.utils import Status
from app.data.create import PlayerCreate
from app.data.update import PlayerUpdate
from app.data.public import PlayerPublic

from app.core.db import get_session
from app.core.logger import logger

router = APIRouter()


@router.get("/", response_model=Page[PlayerPublic])
async def get_players(*, session: Session = Depends(get_session)) -> Page[PlayerPublic]:
    """Get all players"""
    db_players = session.exec(select(Player)).all()
    players = []
    for db_player in db_players:
        teams = db_player.teams
        db_player.teams = []
        player = PlayerPublic.model_validate(db_player)
        player.teams = list(map(lambda x: x.id, teams))
        players.append(player)
    return paginate(players)


@router.get("/{player_id}", response_model=PlayerPublic)
async def get_player(
    *, session: Session = Depends(get_session), player_id: str
) -> PlayerPublic:
    """Get player by id"""
    db_player = session.get(Player, player_id)
    if db_player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    teams = db_player.teams
    db_player.teams = []
    player = PlayerPublic.model_validate(db_player)
    player.teams = list(map(lambda x: x.id, teams))

    return player


@router.post("/")
async def new_player(
    *, session: Session = Depends(get_session), player: PlayerCreate
) -> Status:
    """Create new player"""
    new_player = Player(**player.model_dump())
    with Session(engine) as session:
        session.add(new_player)
        session.commit()
    return Status(status="success")


@router.delete("/{player_id}")
async def delete_player(
    *, session: Session = Depends(get_session), player_id: str
) -> Status:
    """Delete player by id"""
    player = session.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    session.delete(player)
    session.commit()
    return Status(status="success")


@router.put("/{player_id}")
async def update_player(
    *, session: Session = Depends(get_session), player_id: str, new_player: PlayerUpdate
) -> Status:
    """Update player by id"""
    player = session.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    else:
        for field, value in new_player.model_dump().items():
            if value is None:
                continue
            setattr(player, field, value)
        session.add(player)
        session.commit()
        session.refresh(player)
    return Status(status="success")
