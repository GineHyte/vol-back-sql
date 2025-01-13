from typing import List, Optional

from sqlmodel import Field

from app.data.base import (
    TeamBase,
    PlayerBase,
    CoachBase,
    GameBase,
    FileBase,
    TeamToPlayerBase,
    ActionBase,
    TechBase,
    SubtechBase,
    ExerciseBase,
    ExerciseCategoryBase,
    ExerciseTypeBase,
)
from app.data.public import TeamToPlayerPublic


class GameCreate(GameBase):
    pass


class CoachCreate(CoachBase):
    pass


class PlayerCreate(PlayerBase):
    pass


class TeamCreate(TeamBase):
    players: List["TeamToPlayerCreate"] = Field(
        ..., description="List of jsons {player_id: int, team_id: int, amplua: str}"
    )


class TeamToPlayerCreate(TeamToPlayerBase):
    team_id: Optional[int] = Field(None, foreign_key="team.id")
    player_id: Optional[int] = Field(None, foreign_key="player.id")


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


class ExerciseCategoryCreate(ExerciseCategoryBase):
    pass


class ExerciseTypeCreate(ExerciseTypeBase):
    pass

