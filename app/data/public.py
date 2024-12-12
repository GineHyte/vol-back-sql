from typing import List, Optional
from datetime import datetime

from sqlmodel import Field, SQLModel, Relationship

from app.data.utils import Impact
from app.data.relations import TeamToPlayer




class CoachPublic(CoachBase):
    id: Optional[int] = Field(primary_key=True)


class TeamPublic(TeamBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    players: List[Player] = Relationship(
        back_populates="teams", link_model=TeamToPlayer
    )

class GamePublic(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    team_a_score: int = Field(0)
    team_b_score: int = Field(0)
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class TechPublic(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: str
    description: Optional[str]
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class Subtech(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    tech_id: int = Field(..., foreign_key="tech.id")
    name: str
    description: Optional[str]
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class Action(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    game: int = Field(..., foreign_key="game.id")
    team: int = Field(..., foreign_key="team.id")
    player: int = Field(..., foreign_key="player.id")
    subtech: int = Field(..., foreign_key="subtech.id")
    from_zone: int
    to_zone: int
    impact: Impact


class ExerciseCategory(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: str
    description: Optional[str]
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class ExerciseType(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: str
    description: Optional[str]
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class Exercise(SQLModel, table=True):
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


class Status(SQLModel):
    status: Optional[str] = Field(None, description="Status")
    detail: Optional[str] = Field(None, description="Message")
