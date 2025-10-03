from typing import List, Optional

from sqlmodel import Field

from app.data.base import *
from app.data.public import TeamToPlayerPublic


class CoachUpdate(CoachBase):
    first_name: Optional[str] = Field(None, description="First Name")
    last_name: Optional[str] = Field(None, description="Last Name")
    password: Optional[str] = Field(None, description="Password")
    minutes_per_week: Optional[float] = Field(None, description="Minutes per week")
    minutes_per_training: Optional[float] = Field(
        None, description="Minutes per training"
    )


class PlayerUpdate(PlayerBase):
    first_name: Optional[str] = Field(None, description="First Name")
    last_name: Optional[str] = Field(None, description="Last Name")


class GameUpdate(GameBase):
    pass


class TeamUpdate(TeamBase):
    players: Optional[List[TeamToPlayerPublic]] = Field(
        None, description="List of jsons {player: int, amplua: str}"
    )


class ActionUpdate(ActionBase):
    game: Optional[int] = Field(None, description="Game ID")
    team: Optional[int] = Field(None, description="Team ID")
    player: Optional[int] = Field(None, description="Player ID")
    subtech: Optional[int] = Field(None, description="Subtech ID")
    from_zone: Optional[int] = Field(None, description="From zone")
    to_zone: Optional[int] = Field(None, description="To zone")
    impact: Optional[Impact] = Field(None, description="Impact")


class TechUpdate(TechBase):
    pass


class SubtechUpdate(SubtechBase):
    pass


class ExerciseToSubtechUpdate(ExerciseToSubtechBase):
    exercise: Optional[int] = Field(None, description="Exercise id")
    subtech: Optional[int] = Field(None, description="Subtech id")


class ExerciseUpdate(ExerciseBase):
    subtechs: Optional[List[ExerciseToSubtechUpdate]] = Field(
        None, description="Relation between Exercise and Subtech (n to m)"
    )


class UpdateUpdate(UpdateBase):
    pass


class ActionsBatchUpdateOptions(SQLModel):
    actions: List[int] = Field(..., description="List of action IDs to update")
    main_action: ActionUpdate = Field(..., description="Fields to update")
