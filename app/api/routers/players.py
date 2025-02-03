from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session

from app.core.db import engine
from app.data.db import Player
from app.data.utils import Status
from app.data.create import PlayerCreate
from app.data.update import PlayerUpdate
from app.data.public import PlayerPublic, TeamToPlayerPublic
from app.data.utils import NameWithId

from app.core.db import get_session
from app.core.logger import logger

router = APIRouter()


@router.get("/", response_model=Page[PlayerPublic])
async def get_players(*, session: Session = Depends(get_session)) -> Page[PlayerPublic]:
    """Get all players
    
    Returns: 
        Page[PlayerPublic]: list of players
        player.teams: list of teams where player played (see NameWithId and TeamToPlayerPublic)
    """
    db_players = session.exec(select(Player)).all()
    players = []
    for t_player in db_players:
        player = PlayerPublic(**t_player.model_dump(exclude={"teams"}))
        player.teams = []
        for t_team_player in t_player.teams:
            team_player_player = NameWithId(id=t_team_player.player.id, name=t_team_player.player.first_name)
            team_player_team = NameWithId(id=t_team_player.team.id, name=t_team_player.team.name)
            team_player = TeamToPlayerPublic(player=team_player_player, team=team_player_team, amplua=t_team_player.amplua)
            player.teams.append(team_player)
        players.append(player)
    return paginate(players)


@router.get("/{player_id}", response_model=PlayerPublic)
async def get_player(
    *, session: Session = Depends(get_session), player_id: str
) -> PlayerPublic:
    """Get player by id
    
    Returns: 
        PlayerPublic: player
        player.teams: list of teams where player played (see NameWithId and TeamToPlayerPublic)
    """
    db_player = session.get(Player, player_id)

    if db_player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    player = PlayerPublic(**db_player.model_dump(exclude={"teams"}))
    player.teams = []
    for t_team_player in db_player.teams:
        team_player_player = NameWithId(id=t_team_player.player.id, name=t_team_player.player.first_name)
        team_player_team = NameWithId(id=t_team_player.team.id, name=t_team_player.team.name)
        team_player = TeamToPlayerPublic(player=team_player_player, team=team_player_team, amplua=t_team_player.amplua)
        player.teams.append(team_player)

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
