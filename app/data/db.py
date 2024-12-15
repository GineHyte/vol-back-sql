from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Relationship

from app.data.utils import Impact
from app.data.relations import TeamToPlayer
from app.data.base import (
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


class Coach(CoachBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)


class Player(PlayerBase, table=True):
    id: Optional[int] = Field(primary_key=True)
    teams: List["Team"] = Relationship(
        back_populates="players", link_model=TeamToPlayer
    )
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class Team(TeamBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    players: List[Player] = Relationship(
        back_populates="teams", link_model=TeamToPlayer
    )


class Game(GameBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class Tech(TechBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class Subtech(SubtechBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class Action(ActionBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class ExerciseCategory(ExerciseCategoryBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class ExerciseType(ExerciseTypeBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class Exercise(ExerciseBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class File(FileBase, SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
