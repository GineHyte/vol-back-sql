from typing import Optional
from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel
from pydantic import AfterValidator

from app.core.config import settings


datetime_parser = AfterValidator(
    lambda x: datetime.strptime(x, settings.DATETIME_FORMAT)
)

datetime_str = AfterValidator(lambda x: datetime.strftime(x, settings.DATETIME_FORMAT))


class Status(SQLModel):
    status: Optional[str] = Field(None, description="Status")
    detail: Optional[str] = Field(None, description="Message")


class Amplua(Enum):
    DEFENDER = "DEFENDER"
    ATTACKER = "ATTACKER"
    UNIVERSAL = "UNIVERSAL"


class Impact(Enum):
    EFFICIENCY = "EFFICIENCY"
    MISTAKE = "MISTAKE"  # just a mistake
    SCORE = "SCORE"
    FAIL = "FAIL"  # - score


class NameWithId(SQLModel):
    id: Optional[int] = Field(None, description="ID")
    name: Optional[str] = Field(None, description="Name")