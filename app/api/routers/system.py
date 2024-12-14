from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page, paginate
from sqlmodel import select, Session

from app.core.db import engine
from app.data.db import Player
from app.data.utils import Status
from app.data.create import PlayerCreate
from app.data.update import PlayerUpdate
from app.data.public import PlayerPublic

from app.core.db import get_session
from app.core.logger import logger

router = APIRouter()
