from typing import List, Optional

from sqlmodel import Field

from app.data.base import *


class GameCreate(GameBase):
    pass


class CoachCreate(CoachBase):
    first_name: str
    last_name: str
    email: Optional[str] = Field(None, description="Email")
    phone: Optional[str] = Field(None, description="Phone")
    username: str
    password: str
    minutes_per_week: Optional[float] = Field(
        default=0, description="Minutes per week for training"
    )
    minutes_per_training: Optional[float] = Field(
        default=0, description="Minutes per training for coach"
    )


class PlayerCreate(PlayerBase):
    pass


class TeamCreate(TeamBase):
    players: List["TeamToPlayerCreate"] = Field(
        ..., description="List of TeamToPlayer relations"
    )


class TeamToPlayerCreate(TeamToPlayerBase):
    player: Optional[int] = Field(None, description="Player id")
    team: Optional[int] = Field(None, description="Team id")


class FileCreate(FileBase):
    pass


class ActionCreate(ActionBase):
    pass


class TechCreate(TechBase):
    pass


class SubtechCreate(SubtechBase):
    pass


class ExerciseCreate(ExerciseBase):
    exercises: List["ExerciseToSubtechCreate"] = Field(
        ..., description="List of ExerciseToSubtech relations"
    )


class UpdateCreate(UpdateBase):
    pass


class AuthCreate(AuthBase):
    pass


class TokenCreate(SQLModel):
    refresh_token: str = Field(..., description="Refresh Token")
    username: str = Field(..., description="Coach username")


class ExerciseToSubtechCreate(ExerciseToSubtechBase):
    exercise: Optional[int] = Field(None, description="Exercise id")
    subtech: Optional[int] = Field(None, description="Subtech id")