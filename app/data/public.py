from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.data.utils import Impact, Amplua, NameWithId
from app.data.base import *


class CoachPublic(CoachBase):
    id: Optional[int] = Field(None, description="Coach ID")


class PlayerPublic(PlayerBase):
    id: Optional[int] = Field(None, description="Player ID")
    teams: Optional[List["TeamToPlayerPublic"]] = Field(
        None, description="List of TeamToPlayer relations"
    )


class TeamPublic(TeamBase):
    id: int = Field(primary_key=True, description="Team ID")
    players: List["TeamToPlayerPublic"] = Field(
        [], description="List of TeamToPlayer relations"
    )


class GamePublic(GameBase):
    id: int = Field(None, description="Game ID")
    team_a: Optional[NameWithId] = Field(None, description="Team A id")
    team_b: Optional[NameWithId] = Field(None, description="Team B id")


class TechPublic(TechBase):
    id: int = Field(None, description="Tech ID")


class SubtechPublic(SubtechBase):
    id: int = Field(None, description="Subtech ID")
    tech: Optional[NameWithId] = Field(None, description="Tech id")


class ActionPublic(ActionBase):
    id: int = Field(None, description="Action ID")
    game: Optional[NameWithId] = Field(None, description="Game id")
    team: Optional[NameWithId] = Field(None, description="Team id")
    player: Optional[NameWithId] = Field(None, description="Player id")
    subtech: Optional[NameWithId] = Field(None, description="Subtech id")


class ExercisePublic(ExerciseBase):
    id: int = Field(None, description="Exercise ID")
    exercise: List["ExerciseToSubtechPublic"] = Field(
            [], description="List of ExerciseToSubtech relations"
        )


class TeamToPlayerPublic(TeamToPlayerBase):
    team: Optional[NameWithId] = Field(None, description="Team id")
    player: Optional[NameWithId] = Field(None, description="Player id")


class FilePublic(FileBase):
    id: UUID = Field(default_factory=uuid4, primary_key=True)


class UpdatePublic(UpdateBase):
    name: str = Field(..., primary_key=True)


class PlayerSumPublic(SQLModel):
    player: NameWithId = Field(None, description="Player id")
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)

class TechSumPublic(SQLModel):
    player: int = Field(None, description="Player id")
    tech: NameWithId = Field(None, description="Tech id")
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)

class SubtechSumPublic(SQLModel):
    player: int = Field(None, description="Player id")
    tech: int = Field(None, description="Tech id")
    subtech: NameWithId = Field(None, description="Subtech id")
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)

class ImpactSumPublic(SQLModel):
    player: int = Field(None, description="Player id")
    tech: int = Field(None, description="Tech id")
    subtech: int = Field(None, description="Subtech id")
    impact: Impact = Field(None, description="Impact")
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)

class ZoneSumPublic(SQLModel):
    player: int = Field(None, description="Player id")
    tech: int = Field(None, description="Tech id")
    subtech: int = Field(None, description="Subtech id")
    impact: Impact = Field(None, description="Impact")
    zone: str = Field(None, description="Zone")
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)

class PlanWeekPublic(SQLModel):
    exercises: List[ExercisePublic] = Field(None, description="List of exercises")
    week: int = Field(None, description="Week number")

class CoachSessionPublic(CoachSessionBase):
    expires_in: int = Field(..., description="Expiration time in seconds")

class PlayerStatsPublic(SQLModel):
    player_sum: PlayerSumPublic = Field()
    tech_top: List[TechSumPublic] = Field()

class TechStatsPublic(SQLModel):
    tech_top: TechSumPublic = Field()
    subtech_top: List[SubtechSumPublic] = Field()

class SubtechStatsPublic(SQLModel):
    subtech_top: SubtechSumPublic = Field()
    impact_top: List[ImpactSumPublic] = Field()

class ImpactStatsPublic(SQLModel):
    impact_top: ImpactSumPublic = Field()
    zone_top: List[ZoneSumPublic] = Field()

class ExerciseToSubtechPublic(ExerciseToSubtechBase):
    exercise: Optional[NameWithId] = Field(None, description="Exercise id with name")
    subtech: Optional[NameWithId] = Field(None, description="Subtech id with name")