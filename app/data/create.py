from typing import List

from sqlmodel import Field

from app.data.base import TeamBase, PlayerBase, CoachBase, PlayerAmplua


class CoachCreate(CoachBase):
    pass

class PlayerCreate(PlayerBase):
    pass


class TeamCreate(TeamBase):
    players: List[PlayerAmplua] = Field(
        ..., description="List of jsons {player: int, amplua: str}"
    )
