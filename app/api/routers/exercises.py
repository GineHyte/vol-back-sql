from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import paginate
from sqlmodel import select, Session, delete, col

from app.core.db import engine, get_session
from app.data.db import Exercise, Subtech, Tech, ExerciseToSubtech
from app.core.logger import logger
from app.data.utils import Status, NameWithId
from app.data.update import ExerciseUpdate
from app.data.create import ExerciseCreate
from app.data.public import ExercisePublic, ExerciseToSubtechPublic
from app.api.deps import VolPage

router = APIRouter()


@router.get("/")
async def get_exercises(
    *, session: Session = Depends(get_session)
) -> VolPage[ExercisePublic]:
    """Get all exercises"""
    db_exercises = session.exec(select(Exercise)).all()
    exersises = []
    for db_exercise in db_exercises:
        exercise = ExercisePublic(**db_exercise.model_dump(exclude=["subtech", "tech"]))
        exercise.subtechs = []
        for exr_to_sub in db_exercise.subtechs:
            subtech = NameWithId(id=exr_to_sub.subtech.id, name=exr_to_sub.subtech.name)
            exr_to_sub_public = ExerciseToSubtechPublic(subtech=subtech)
            exercise.subtechs.append(exr_to_sub_public)
        exersises.append(exercise)
    return paginate(exersises)


@router.get("/{exercise_id}")
async def get_exercise(
    *, session: Session = Depends(get_session), exercise_id: str
) -> ExercisePublic:
    """
    Retrieve an exercise by its ID.

    Args:
        session (Session): The database session dependency.
        exercise_id (str): The unique identifier of the exercise to retrieve.

    Returns:
        ExercisePublic: The public representation of the exercise, including its
        associated subtech and tech details.

    Raises:
        HTTPException: If the exercise with the given ID is not found, raises a 404 error.
    """
    """Get exercise by id"""
    db_exercise = session.get(Exercise, exercise_id)
    if not db_exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    exercise = ExercisePublic(**db_exercise.model_dump(exclude=["subtech", "tech"]))
    exercise.subtechs = []
    for exr_to_sub in db_exercise.subtechs:
        subtech = NameWithId(id=exr_to_sub.subtech.id, name=exr_to_sub.subtech.name)
        exr_to_sub_public = ExerciseToSubtechPublic(subtech=subtech)
        exercise.subtechs.append(exr_to_sub_public)
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
