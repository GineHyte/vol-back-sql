from typing import List, Optional
from datetime import datetime

from sqlmodel import Field, SQLModel, Relationship

from app.data.utils import SQLModelID, Amplua, Impact


class TeamToPlayer(SQLModel, table=True):
    team_id: Optional[int] = Field(None, foreign_key="team.id", primary_key=True)
    player_id: Optional[int] = Field(None, foreign_key="player.id", primary_key=True)
    amplua: Amplua


class PlayerBase(SQLModel):
    first_name: str
    last_name: str
    age: Optional[int] = Field(None, description="Age")
    height: Optional[float] = Field(None, description="Height")
    weight: Optional[float] = Field(None, description="Weight")
    image_url: Optional[str] = Field(None, description="Image URL")
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class PlayerUpdate(PlayerBase):
    first_name: Optional[str] = Field(None, description="First Name")
    last_name: Optional[str] = Field(None, description="Last Name")


class PlayerCreate(PlayerBase):
    pass


class Player(PlayerBase, SQLModelID):
    pass


class CoachBase(SQLModel):
    first_name: str
    last_name: str
    email: Optional[str] = Field(None, description="Email")
    phone: Optional[str] = Field(None, description="Phone")
    username: str
    password: str
    minutes_per_week: float = Field(default=0)
    minutes_per_training: float = Field(default=0)


class CoachUpdate(CoachBase):
    first_name: Optional[str] = Field(None, description="First Name")
    last_name: Optional[str] = Field(None, description="Last Name")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, description="Password")


class CoachCreate(CoachBase):
    pass


class Coach(CoachBase, SQLModelID):
    pass


class TeamBase(SQLModel):
    name: str
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class TeamUpdate(TeamBase):
    pass


class TeamCreate(TeamBase):
    pass


class Team(TeamBase, SQLModelID):
    id: Optional[int] = Field(None, primary_key=True)
    name: str
    players: List[Player] = Relationship(
        back_populates="teams", link_model=TeamToPlayer
    )
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class GameBase(SQLModel):
    name: str
    description: Optional[str]
    from_datetime: Optional[datetime]
    to_datetime: Optional[datetime]
    team_a_id: str = Field(..., foreign_key="team.id")
    team_b_id: str = Field(..., foreign_key="team.id")


class Game(SQLModelID):
    id: Optional[int] = Field(None, primary_key=True)
    team_a_score: int = Field(0)
    team_b_score: int = Field(0)
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class Tech(SQLModelID):
    id: Optional[int] = Field(None, primary_key=True)
    name: str
    description: Optional[str]
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class Subtech(SQLModelID):
    id: Optional[int] = Field(None, primary_key=True)
    tech_id: int = Field(..., foreign_key="tech.id")
    name: str
    description: Optional[str]
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class Action(SQLModelID):
    id: Optional[int] = Field(None, primary_key=True)
    game: int = Field(..., foreign_key="game.id")
    team: int = Field(..., foreign_key="team.id")
    player: int = Field(..., foreign_key="player.id")
    subtech: int = Field(..., foreign_key="subtech.id")
    from_zone: int
    to_zone: int
    impact: Impact


class Exercise(SQLModelID):
    id: Optional[int] = Field(None, primary_key=True)
    name: str
    description: Optional[str]
    subtech_id: int = Field(..., foreign_key="subtech.id")
    coach_id: int = Field(..., foreign_key="coach.id")
    image_url: Optional[str]
    video_url: Optional[str]
    difficulty: int
    category_id: int = Field(..., foreign_key="exercise_category.id")
    type_id: int = Field(..., foreign_key="exercise_type.id")


class ExerciseCategory(SQLModelID):
    id: Optional[int] = Field(None, primary_key=True)
    name: str
    description: Optional[str]
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class ExerciseType(SQLModelID):
    id: Optional[int] = Field(None, primary_key=True)
    name: str
    description: Optional[str]
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class Status(SQLModel):
    status: str
    message: str
