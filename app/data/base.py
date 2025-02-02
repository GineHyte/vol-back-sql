from typing import Optional
from datetime import datetime
from uuid import UUID


from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.data.utils import Impact, Amplua


class CoachBase(SQLModel):
    first_name: str
    last_name: str
    email: Optional[str] = Field(None, description="Email")
    phone: Optional[str] = Field(None, description="Phone")
    username: str
    password: str
    minutes_per_week: float = Field(default=0)
    minutes_per_training: float = Field(default=0)


class PlayerBase(SQLModel):
    first_name: str
    last_name: str
    age: Optional[int] = Field(None, description="Age")
    height: Optional[float] = Field(None, description="Height")
    weight: Optional[float] = Field(None, description="Weight")
    image_file: Optional[UUID] = Field(
        None, description="Image UUID file", foreign_key="file.id"
    )


class TeamBase(SQLModel):
    name: str
    coach: Optional[int] = Field(None, foreign_key="coach.id")


class GameBase(SQLModel):
    name: str = Field(..., description="Name")
    description: Optional[str] = Field(None, description="Description")
    from_datetime: Optional[datetime] = Field(None, description="Start datetime")
    to_datetime: Optional[datetime] = Field(None, description="End datetime")
    team_a: int = Field(..., foreign_key="team.id")
    team_b: int = Field(..., foreign_key="team.id")

    @field_validator("from_datetime", "to_datetime", mode="before")
    def datetime_validator(cls, v) -> Optional[datetime]:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(v)


class TechBase(SQLModel):
    name: str
    description: Optional[str]


class SubtechBase(SQLModel):
    tech: int = Field(..., foreign_key="tech.id")
    name: str
    description: Optional[str]
    difficulty: int = Field(..., description="Difficulty", ge=1, le=3)


class ActionBase(SQLModel):
    game: int = Field(..., foreign_key="game.id")
    team: int = Field(..., foreign_key="team.id")
    player: int = Field(..., foreign_key="player.id")
    subtech: int = Field(..., foreign_key="subtech.id")
    from_zone: int
    to_zone: int
    impact: Impact


class ExerciseBase(SQLModel):
    name: str
    description: Optional[str]
    tech: int = Field(..., foreign_key="tech.id")
    subtech: int = Field(..., foreign_key="subtech.id")
    image_url: Optional[str] = Field(None, description="Image URL")
    video_url: Optional[str] = Field(None, description="Video URL")
    difficulty: int
    exercises_for_learning: bool = Field(False)
    exercises_for_consolidation: bool = Field(False)
    exercises_for_improvement: bool = Field(False)
    simulation_exercises: bool = Field(False)
    exercises_with_the_ball_on_your_own: bool = Field(False)
    exercises_with_the_ball_in_pairs: bool = Field(False)
    exercises_with_the_ball_in_groups: bool = Field(False)
    exercises_in_difficult_conditions: bool = Field(False)
    from_zone: Optional[int] = Field(None)
    to_zone: Optional[int] = Field(None)
    time_per_exercise: int


class FileBase(SQLModel):
    data: bytes = Field(..., description="File data")


class TeamToPlayerBase(SQLModel):
    team: int = Field(..., foreign_key="team.id")
    player: int = Field(..., foreign_key="player.id")
    amplua: Amplua


class UpdateBase(SQLModel):
    url: str
    notes: str
    pub_date: datetime
