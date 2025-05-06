from typing import List, Optional

from sqlmodel import Field

from app.data.base import *


class GameCreate(GameBase):
    pass


class CoachCreate(CoachBase):
    pass


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
    pass


class UpdateCreate(UpdateBase):
    pass

class AuthCreate(AuthBase):
    pass

class TokenCreate(SQLModel):
    refresh_token: str = Field(..., description="Refresh Token")
    username: str = Field(..., description="Coach username")