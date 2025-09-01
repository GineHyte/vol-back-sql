from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Relationship

from app.data.utils import Impact, Amplua
from app.data.base import *


class TeamToPlayer(TeamToPlayerBase, SQLModel, table=True):
    team_id: int = Field(
        None, foreign_key="team.id", primary_key=True, ondelete="CASCADE"
    )
    player_id: int = Field(
        None, foreign_key="player.id", primary_key=True, ondelete="CASCADE"
    )
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
    coach: Optional[int] = Field(None, foreign_key="coach.id", ondelete="CASCADE")


class Team(TeamBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    players: List[TeamToPlayer] = Relationship(
        back_populates="team", cascade_delete=True
    )
    coach: Optional[int] = Field(None, foreign_key="coach.id", ondelete="CASCADE")


class Game(GameBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    coach: Optional[int] = Field(None, foreign_key="coach.id", ondelete="CASCADE")


class Tech(TechBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    coach: Optional[int] = Field(None, foreign_key="coach.id", ondelete="CASCADE")


class Subtech(SubtechBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    coach: Optional[int] = Field(None, foreign_key="coach.id", ondelete="CASCADE")
    exercises: List["ExerciseToSubtech"] = Relationship(
        back_populates="subtech", cascade_delete=True
    )


class Action(ActionBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    game: Optional[int] = Field(None, foreign_key="game.id", ondelete="CASCADE")
    coach: Optional[int] = Field(None, foreign_key="coach.id", ondelete="CASCADE")


class Exercise(ExerciseBase, SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    coach: Optional[int] = Field(None, foreign_key="coach.id", ondelete="CASCADE")
    subtechs: List["ExerciseToSubtech"] = Relationship(
        back_populates="exercise", cascade_delete=True
    )


class File(FileBase, SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)


class Update(UpdateBase, SQLModel, table=True):
    name: str = Field(..., primary_key=True)


class CoachSession(CoachSessionBase, SQLModel, table=True):
    coach: int = Field(..., foreign_key="coach.id", ondelete="CASCADE")
    expires_at: int = Field(..., description="Session expiration timestamp")


class ExerciseToSubtech(ExerciseToSubtechBase, SQLModel, table=True):
    exercise_id: int = Field(
        None, foreign_key="exercise.id", primary_key=True, ondelete="CASCADE"
    )
    subtech_id: int = Field(
        None, foreign_key="subtech.id", primary_key=True, ondelete="CASCADE"
    )
    exercise: Exercise = Relationship(back_populates="subtechs")
    subtech: Subtech = Relationship(back_populates="exercises")
