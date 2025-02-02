from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.data.utils import Impact, Amplua, NameWithId
from app.data.base import *


class CoachPublic(CoachBase):
    id: Optional[int] = Field(None, description="Coach ID")


class PlayerPublic(PlayerBase):
    id: Optional[int] = Field(None, description="Player ID")
    teams: Optional[List["TeamToPlayerPublic"]] = Field(
        None, description="List of TeamToPlayer relations"
    )


class TeamPublic(TeamBase):
    id: int = Field(primary_key=True, description="Team ID")
    players: List["TeamToPlayerPublic"] = Field(
        ..., description="List of TeamToPlayer relations"
    )


class GamePublic(GameBase):
    id: int = Field(None, description="Game ID")
    team_a: NameWithId
    team_b: NameWithId

class TechPublic(TechBase):
    id: int = Field(None, description="Tech ID")
    pass

class SubtechPublic(SubtechBase):
    id: int = Field(None, description="Subtech ID")
    tech: NameWithId

class ActionPublic(ActionBase):
    id: int = Field(None, description="Action ID")
    game: NameWithId
    team: NameWithId
    player: NameWithId
    subtech: NameWithId


class ExercisePublic(ExerciseBase):
    id: int = Field(None, description="Exercise ID")
    subtech: NameWithId
    tech: NameWithId


class TeamToPlayerPublic(TeamToPlayerBase):
    team: NameWithId
    player: NameWithId 


class FilePublic(FileBase):
    id: UUID = Field(default_factory=uuid4, primary_key=True)


class UpdatePublic(UpdateBase):
    name: str = Field(..., primary_key=True)
