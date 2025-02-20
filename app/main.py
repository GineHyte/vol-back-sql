from fastapi import FastAPI
from fastapi_pagination import add_pagination
from fastapi_pagination.utils import disable_installed_extensions_check
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import logger
from app.api.main import api_router
from app.core.db import init_db
from app.core.logger import init_logfire, logger
from app.core.search import init_search

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
)
add_pagination(app)
disable_installed_extensions_check()

init_db()
init_search()
logger.info("Database initialized")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.LOGFIRE:
    init_logfire(app)

app.include_router(api_router)
logger.info("API routes included")