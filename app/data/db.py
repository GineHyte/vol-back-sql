from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Relationship

from app.data.utils import Impact, Amplua
from app.data.base import *


class TeamToPlayer(TeamToPlayerBase, SQLModel, table=True):
    team_id: int = Field(None, foreign_key="team.id", primary_key=True)
    player_id: int = Field(None, foreign_key="player.id", primary_key=True)
    amplua: Amplua

    team: "Team" = Relationship(back_populates="players")
    player: "Player" = Relationship(back_populates="teams")


class Coach(CoachBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)


class Player(PlayerBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    teams: List[TeamToPlayer] = Relationship(
        back_populates="player", cascade_delete=True
    )
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class Team(TeamBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    players: List[TeamToPlayer] = Relationship(
        back_populates="team", cascade_delete=True
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


class Update(UpdateBase, SQLModel, table=True):
    name: str = Field(..., primary_key=True)
