from typing import List

from sqlmodel import Field

from app.data.base import TeamBase, PlayerBase, CoachBase, GameBase
from app.data.public import TeamToPlayerPublic


class GameCreate(GameBase):
    pass


class CoachCreate(CoachBase):
    pass


class PlayerCreate(PlayerBase):
    pass


class TeamCreate(TeamBase):
    players: List[TeamToPlayerPublic] = Field(
        ..., description="List of jsons {player_id: int, team_id: int, amplua: str}"
    )
