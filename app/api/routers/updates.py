from typing import Annotated, List

import aiofiles
from starlette.responses import FileResponse
from fastapi import APIRouter, Depends, UploadFile, HTTPException, File
from sqlmodel import Session, select

from app.data.public import UpdatePublic
from app.data.db import Update
from app.data.utils import Status
from app.core.db import get_session

router = APIRouter()


@router.post("/releases")
async def upload_release(release: UploadFile) -> Status:
    """Create new release"""
    try:
        print(release)
        content = await release.read()  # async read
        async with aiofiles.open(f"files/releases/{release.filename}", "wb") as f:
            await f.write(content)  # async write
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading release: {e}")
    finally:
        release.file.close()

    return Status(status="success", detail="Release created")


@router.get("/releases/{release_id}")
async def get_releases(release_id: str) -> FileResponse:
    """Get new release"""
    return FileResponse(f"files/releases/{release_id}", filename=release_id)


@router.post("/")
async def post_update(
    *, update: UpdatePublic, session: Session = Depends(get_session)
) -> Status:
    """Post update"""
    update_db = Update(**update.model_dump())

    session.add(update_db)
    session.commit()

    return Status(status="success", detail="Update created")


@router.get("/")
async def get_updates(*, session: Session = Depends(get_session)) -> List[UpdatePublic]:
    """Get updates"""
    updates = session.exec(select(Update)).all()
    return updates


@router.get("/{update_id}")
async def get_update(
    *, update_id: str, session: Session = Depends(get_session)
) -> UpdatePublic:
    """Get update"""
    update = session.get(Update, update_id)
    if not update:
        raise HTTPException(status_code=404, detail="Update not found")
    return update
