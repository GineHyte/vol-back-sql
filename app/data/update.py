from typing import List, Optional

from sqlmodel import Field

from app.data.base import TeamBase, PlayerBase, GameBase, CoachBase, PlayerAmplua


class CoachUpdate(CoachBase):
    first_name: Optional[str] = Field(None, description="First Name")
    last_name: Optional[str] = Field(None, description="Last Name")
    password: Optional[str] = Field(None, description="Password")
    minutes_per_week: Optional[float] = Field(None, description="Minutes per week")
    minutes_per_training: Optional[float] = Field(
        None, description="Minutes per training"
    )


class PlayerUpdate(PlayerBase):
    first_name: Optional[str] = Field(None, description="First Name")
    last_name: Optional[str] = Field(None, description="Last Name")


class GameUpdate(GameBase):
    name: Optional[str] = Field(None, description="Name")
    team_a_id: Optional[str] = Field(..., foreign_key="team.id")
    team_b_id: Optional[str] = Field(..., foreign_key="team.id")


class TeamUpdate(TeamBase):
    players: Optional[List[PlayerAmplua]] = Field(
        None, description="List of jsons {player: int, amplua: str}"
    )