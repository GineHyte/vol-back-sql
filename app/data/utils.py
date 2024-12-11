from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import AfterValidator
from sqlmodel import SQLModel, Field

from app.core.config import settings


class SQLModelID(SQLModel):
    id: UUID = Field(default=uuid4(), primary_key=True, description="Unique identifier")


datetime_parser = AfterValidator(lambda x: datetime.strptime(x, settings.DATETIME_FORMAT))

datetime_str = AfterValidator(lambda x: datetime.strftime(x, settings.DATETIME_FORMAT))


class Amplua(Enum):
    DEFENDER = "Defender"
    ATACKER = "Atacker"
    UNIVERSAL = "Universal"


class Impact(Enum):
    EFFEIENCY = "Effeiency"
    MISTAKE = "Mistake"
