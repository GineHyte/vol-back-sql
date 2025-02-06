from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session, delete, col

from app.core.db import engine, get_session
from app.data.db import Exercise, Subtech, Tech
from app.data.utils import Status, NameWithId
from app.data.update import ExerciseUpdate
from app.data.create import ExerciseCreate
from app.data.public import ExercisePublic
from app.core.logger import logger


router = APIRouter()


@router.get("/")
async def get_exercises(
    *, session: Session = Depends(get_session)
) -> Page[ExercisePublic]:
    """Get all exercises"""
    db_exercises = session.exec(select(Exercise)).all()
    exersises = []
    for db_exercise in db_exercises:
        exercise = ExercisePublic(**db_exercise.model_dump(exclude=["subtech", "tech"]))
        exercise.subtech = NameWithId(
            id=db_exercise.subtech, name=session.get(Subtech, db_exercise.subtech).name
        )
        exercise.tech = NameWithId(
            id=db_exercise.tech, name=session.get(Tech, db_exercise.tech).name
        )
        exersises.append(exercise)
    return paginate(exersises)


@router.get("/{exercise_id}")
async def get_exercise(
    *, session: Session = Depends(get_session), exercise_id: str
) -> ExercisePublic:
    """Get exercise by id"""
    db_exercise = session.get(Exercise, exercise_id)
    if not db_exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    exercise = ExercisePublic(**db_exercise.model_dump(exclude=["subtech", "tech"]))
    exercise.subtech = NameWithId(
        id=db_exercise.subtech, name=session.get(Subtech, db_exercise.subtech).name
    )
    exercise.tech = NameWithId(
        id=db_exercise.tech, name=session.get(Tech, db_exercise.tech).name
    )
    return exercise


@router.post("/", response_model=Status)
async def create_exercise(
    *, session: Session = Depends(get_session), new_exercise: ExerciseCreate
) -> Status:
    """Create new exercise"""
    exercise = Exercise(**new_exercise.model_dump())
    session.add(exercise)
    session.commit()
    return Status(status="success", detail="Exercise created")


@router.delete("/{exercise_id}")
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


@router.put("/{exercise_id}")
async def update_exercise(
    *,
    session: Session = Depends(get_session),
    exercise_id: str,
    new_exercise: ExerciseUpdate
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
