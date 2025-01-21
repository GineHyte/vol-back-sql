from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session, delete, col

from app.core.db import engine, get_session
from app.data.db import Exercise
from app.data.utils import Status
from app.data.update import ExerciseUpdate
from app.data.create import ExerciseCreate
from app.data.public import ExercisePublic
from app.core.logger import logger


router = APIRouter()


@router.get("/", response_model=Page[Exercise])
async def get_exercises(*, session: Session = Depends(get_session)) -> Page[Exercise]:
    """Get all exercises"""
    return paginate(session.exec(select(Exercise)).all())


@router.get("/{exercise_id}")
async def get_exercise(*, session: Session = Depends(get_session), exercise_id: str) -> Exercise:
    """Get exercise by id"""
    db_exercise = session.get(Exercise, exercise_id)
    if not db_exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return db_exercise


@router.post("/", response_model=Status)
async def create_exercise(
    *, session: Session = Depends(get_session), new_exercise: ExerciseCreate
) -> Status:
    """Create new exercise"""
    exercise = Exercise(**new_exercise.model_dump())
    session.add(exercise)
    session.commit()
    return Status(status="success", detail="Exercise created")


@router.delete("/{tech_id}")
async def delete_exercise(
    *, session: Session = Depends(get_session), exercise_id: str
) -> Status:
    """Delete exercise by id"""
    exercise = session.get(Exercise, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    session.delete(exercise)
    session.commit()
    return Status(status="success", detail="Exercise deleted")


@router.put("/{tech_id}")
async def update_exercise(
    *, session: Session = Depends(get_session), exercise_id: str, new_exercise: ExerciseUpdate
) -> Status:
    """Update exercise by id"""
    exercise = session.get(Exercise, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")

    for field, value in new_exercise.model_dump(exclude_none=True).items():
        setattr(exercise, field, value)

    session.add(exercise)
    session.commit()

    return Status(status="success", detail="Exercise updated")
