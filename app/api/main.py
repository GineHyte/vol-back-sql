from fastapi import APIRouter

from app.api.routers import games, players, teams

api_router = APIRouter()
api_router.include_router(games.router, tags=["login"])
api_router.include_router(players.router, prefix="/users", tags=["users"])
api_router.include_router(teams.router, prefix="/utils", tags=["utils"])
