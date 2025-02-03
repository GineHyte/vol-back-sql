from typing import List, Optional

from sqlmodel import Field

from app.data.base import *
from app.data.public import TeamToPlayerPublic
from app.data.utils import NameWithId


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
    team: NameWithId
    player: NameWithId 


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
