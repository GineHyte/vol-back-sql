from typing import Optional
from datetime import datetime
from uuid import UUID


from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.data.utils import Impact


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
    image_file_id: Optional[UUID] = Field(
        None, description="Image UUID file", foreign_key="file.id"
    )


class TeamBase(SQLModel):
    name: str
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class GameBase(SQLModel):
    name: str = Field(..., description="Name")
    description: Optional[str] = Field(None, description="Description")
    from_datetime: Optional[datetime] = Field(None, description="Start datetime")
    to_datetime: Optional[datetime] = Field(None, description="End datetime")
    team_a: int = Field(..., foreign_key="team.id")
    team_b: int = Field(..., foreign_key="team.id")

    @field_validator("from_datetime", "to_datetime", mode="before")
    def datetime_validator(cls, v) -> datetime:
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(v)


class TechBase(SQLModel):
    name: str
    description: Optional[str]


class SubtechBase(SQLModel):
    tech_id: int = Field(..., foreign_key="tech.id")
    name: str
    description: Optional[str]


class ActionBase(SQLModel):
    game: int = Field(..., foreign_key="game.id")
    team: int = Field(..., foreign_key="team.id")
    player: int = Field(..., foreign_key="player.id")
    subtech: int = Field(..., foreign_key="subtech.id")
    from_zone: int
    to_zone: int
    impact: Impact


class ExerciseCategoryBase(SQLModel):
    name: str
    description: Optional[str]


class ExerciseTypeBase(SQLModel):
    name: str
    description: Optional[str]


class ExerciseBase(SQLModel):
    name: str
    description: Optional[str]
    subtech_id: int = Field(..., foreign_key="subtech.id")
    image_url: Optional[str]
    video_url: Optional[str]
    difficulty: int
    category_id: int = Field(..., foreign_key="exercisecategory.id")
    type_id: int = Field(..., foreign_key="exercisetype.id")


class FileBase(SQLModel):
    data: bytes = Field(..., description="File data")
