from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import AfterValidator
from sqlmodel import SQLModel, Field

from app import DATETIME_FORMAT


class SQLModelID(SQLModel, table=True):
    id: UUID = Field(default=uuid4(), primary_key=True, description="Unique identifier")


datetime_parser = AfterValidator(lambda x: datetime.strptime(x, DATETIME_FORMAT))

datetime_str = AfterValidator(lambda x: datetime.strftime(x, DATETIME_FORMAT))


class Amplua(StrEnum):
    DEFENDER = "Defender"
    ATACKER = "Atacker"
    UNIVERSAL = "Universal"


class Impact(StrEnum):
    EFFEIENCY = "Effeiency"
    MISTAKE = "Mistake"
