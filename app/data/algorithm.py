from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Relationship

from app.data.utils import Impact


class PlayerSum(SQLModel, table=True):
    player: int = Field(primary_key=True)
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)


class TechSum(SQLModel, table=True):
    player: int = Field(primary_key=True)
    tech: int = Field(primary_key=True)
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)


class SubtechSum(SQLModel, table=True):
    player: int = Field(primary_key=True)
    tech: int = Field(primary_key=True)
    subtech: int = Field(primary_key=True)
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)


class ImpactSum(SQLModel, table=True):
    player: int = Field(primary_key=True)
    tech: int = Field(primary_key=True)
    subtech: int = Field(primary_key=True)
    impact: Impact = Field(primary_key=True)
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)


class ZoneSum(SQLModel, table=True):
    player: int = Field(primary_key=True)
    tech: int = Field(primary_key=True)
    subtech: int = Field(primary_key=True)
    impact: int = Field(primary_key=True)
    zone: str = Field(primary_key=True)
    sum_actions: int = Field(default=0)
    prozent: float = Field(default=0)
