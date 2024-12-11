from typing import Optional

from sqlmodel import Field, SQLModel

from app.data.models import Amplua


class TeamToPlayer(SQLModel, table=True):
    team_id: Optional[int] = Field(None, foreign_key="team.id", primary_key=True)
    player_id: Optional[int] = Field(None, foreign_key="player.id", primary_key=True)
    amplua: Amplua