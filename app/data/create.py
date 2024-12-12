from typing import List

from sqlmodel import Field

from app.data.base import TeamBase, PlayerBase, CoachBase
from app.data.public import TeamToPlayerPublic


class CoachCreate(CoachBase):
    pass


class PlayerCreate(PlayerBase):
    pass


class TeamCreate(TeamBase):
    players: List[TeamToPlayerPublic] = Field(
        ..., description="List of jsons {player_id: int, team_id: int, amplua: str}"
    )
