from typing import Optional
from sqlmodel import Field, SQLModel

from app.data.utils import SQLModelID


class PlayerBase(SQLModel):
    first_name: str
    last_name: str
    age: Optional[int] = Field(None, description="Age")
    height: Optional[float] = Field(None, description="Height")
    weight: Optional[float] = Field(None, description="Weight")
    image_url: Optional[str] = Field(None, description="Image URL")
    coach_id: Optional[int] = Field(None, foreign_key="coach.id")


class PlayerUpdate(PlayerBase):
    first_name: Optional[str] = Field(None, description="First Name")
    last_name: Optional[str] = Field(None, description="Last Name")


class PlayerCreate(PlayerBase):
    pass


class Player(PlayerBase, SQLModelID):
    pass
