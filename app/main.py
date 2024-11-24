from contextlib import asynccontextmanager
import logging, sys

from fastapi import FastAPI
from fastapi_pagination import add_pagination
from fastapi.middleware.cors import CORSMiddleware

from app import MONGO_URI, projectConfig
from app.routers import games, teams, players
from app.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(MONGO_URI)

    try:
        await init_beanie(
            database=client.get_default_database(),
            document_models=Document.__subclasses__() + UnionDoc.__subclasses__(),
        )
    except Exception as e:
        logger.error("Error initializing Beanie: %s", e)

    yield


app = FastAPI(
    title=projectConfig.__projname__,
    version=projectConfig.__version__,
    description=projectConfig.__description__,
    lifespan=lifespan,
)
add_pagination(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(players.router)
app.include_router(games.router)
app.include_router(teams.router)
