from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session

from app.core.db import engine
from app.data.db import File
from app.data.utils import Status
from app.data.create import FileCreate
from app.data.public import FilePublic
from app.core.db import get_session
from app.core.logger import logger

from app.api.routers import algorithm

router = APIRouter()


@router.get("/files", response_model=Page[FilePublic])
def get_files(*, session: Session = Depends(get_session)) -> Page[FilePublic]:
    files = session.exec(select(File)).all()
    return paginate(files)


@router.get("/files/{file_id}", response_model=FilePublic)
def get_file(*, session: Session = Depends(get_session), file_id: UUID) -> FilePublic:
    file = session.get(File, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.post("/files", response_model=Status)
def create_file(*, session: Session = Depends(get_session), file: FileCreate) -> Status:
    new_file = File(**file.model_dump())
    session.add(new_file)
    session.commit()
    return Status(status="success", detail=str(new_file.id))


@router.get("/test/{player_id}")
async def test(player_id: int):
    logger.info("Test")
    await algorithm.calculate_sums(player_id)
    return {"status": "ok"}