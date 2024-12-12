from typing import Optional
from datetime import datetime

from sqlmodel import Field, SQLModel


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
    image_url: Optional[str] = Field(None, description="Image URL")


class TeamBase(SQLModel):
    name: str
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class GameBase(SQLModel):
    name: str
    description: Optional[str]
    from_datetime: Optional[datetime]
    to_datetime: Optional[datetime]
    team_a_id: str = Field(..., foreign_key="team.id")
    team_b_id: str = Field(..., foreign_key="team.id")


