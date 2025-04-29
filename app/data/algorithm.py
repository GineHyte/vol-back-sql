from datetime import datetime
from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.data.utils import Impact


class PlayerSum(SQLModel, table=True):
    player: int = Field(primary_key=True, foreign_key="player.id", ondelete="CASCADE")
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)


class TechSum(SQLModel, table=True):
    player: int = Field(primary_key=True, foreign_key="player.id", ondelete="CASCADE")
    tech: int = Field(primary_key=True)
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)


class SubtechSum(SQLModel, table=True):
    player: int = Field(primary_key=True, foreign_key="player.id", ondelete="CASCADE")
    tech: int = Field(primary_key=True)
    subtech: int = Field(primary_key=True)
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)


class ImpactSum(SQLModel, table=True):
    player: int = Field(primary_key=True, foreign_key="player.id", ondelete="CASCADE")
    tech: int = Field(primary_key=True)
    subtech: int = Field(primary_key=True)
    impact: Impact = Field(primary_key=True)
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)


class ZoneSum(SQLModel, table=True):
    player: int = Field(primary_key=True, foreign_key="player.id", ondelete="CASCADE")
    tech: int = Field(primary_key=True)
    subtech: int = Field(primary_key=True)
    impact: int = Field(primary_key=True)
    zone: str = Field(primary_key=True)
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)


class Plan(SQLModel, table=True):
    player: int = Field(foreign_key="player.id", ondelete="CASCADE", primary_key=True)
    id: int = Field(primary_key=True)
    start_date: datetime = Field()

    @field_validator("start_date", mode="before")
    def datetime_validator(cls, v) -> Optional[datetime]:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(v)


class PlanWeek(SQLModel, table=True):
    player: int = Field(foreign_key="player.id", ondelete="CASCADE", primary_key=True)
    plan: int = Field(primary_key=True, foreign_key="plan.id", ondelete="CASCADE")
    week: int = Field(primary_key=True)

class PlanExercise(SQLModel, table=True):
    player: int = Field(foreign_key="player.id", ondelete="CASCADE")
    plan: int = Field(primary_key=True, foreign_key="plan.id", ondelete="CASCADE")
    week: int = Field(primary_key=True, foreign_key="planweek.week", ondelete="CASCADE")
    id: int = Field(primary_key=True)
    exercise: int = Field(foreign_key="exercise.id", ondelete="CASCADE")