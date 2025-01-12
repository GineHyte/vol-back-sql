from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.data.utils import Impact, Amplua
from app.data.base import (
    TeamToPlayerBase,
    CoachBase,
    PlayerBase,
    TeamBase,
    GameBase,
    TechBase,
    SubtechBase,
    ActionBase,
    ExerciseCategoryBase,
    ExerciseTypeBase,
    ExerciseBase,
    FileBase,
)


class CoachPublic(CoachBase):
    id: Optional[int] = Field(None, description="Coach ID")


class PlayerPublic(PlayerBase):
    id: Optional[int] = Field(None, description="Player ID")
    teams: Optional[List["TeamToPlayerPublic"]] = Field(
        None, description="List of TeamToPlayer relations"
    )


class TeamPublic(TeamBase):
    id: Optional[int] = Field(primary_key=True, description="Team ID")
    players: List["TeamToPlayerPublic"] = Field(
        ..., description="List of TeamToPlayer relations"
    )


class GamePublic(GameBase):
    id: Optional[int] = Field(primary_key=True)
    team_a_score: int = Field(0)
    team_b_score: int = Field(0)
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class TechPublic(TechBase):
    id: Optional[int] = Field(primary_key=True)
    name: str
    description: Optional[str]
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class SubtechPublic(SubtechBase):
    id: Optional[int] = Field(primary_key=True)
    tech_id: int = Field(..., foreign_key="tech.id")
    name: str
    description: Optional[str]
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class ActionPublic(ActionBase):
    id: Optional[int] = Field(primary_key=True)
    game: int = Field(..., foreign_key="game.id")
    team: int = Field(..., foreign_key="team.id")
    player: int = Field(..., foreign_key="player.id")
    subtech: int = Field(..., foreign_key="subtech.id")
    from_zone: int
    to_zone: int
    impact: Impact


class ExerciseCategoryPublic(ExerciseCategoryBase):
    id: Optional[int] = Field(primary_key=True)
    name: str
    description: Optional[str]
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class ExerciseTypePublic(ExerciseTypeBase):
    id: Optional[int] = Field(primary_key=True)
    name: str
    description: Optional[str]
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class ExercisePublic(ExerciseBase):
    id: Optional[int] = Field(primary_key=True)
    name: str
    description: Optional[str]
    subtech_id: int = Field(..., foreign_key="subtech.id")
    coach_id: int = Field(..., foreign_key="coach.id")
    image_url: Optional[str]
    video_url: Optional[str]
    difficulty: int
    category_id: int = Field(..., foreign_key="exercisecategory.id")
    type_id: int = Field(..., foreign_key="exercisetype.id")


class TeamToPlayerPublic(TeamToPlayerBase):
    pass


class FilePublic(FileBase):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
