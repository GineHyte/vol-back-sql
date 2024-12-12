from typing import List

from sqlmodel import Field

from app.data.base import TeamBase, PlayerBase, CoachBase
from app.data.utils import PlayerAmplua


class CoachCreate(CoachBase):
    pass

class PlayerCreate(PlayerBase):
    pass


class TeamCreate(TeamBase):
    players: List[PlayerAmplua] = Field(
        ..., description="List of jsons {player: int, amplua: str}"
    )
