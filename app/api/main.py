from fastapi import APIRouter

from app.api.routers import games, players, teams, system

api_router = APIRouter()
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(games.router, prefix="/games", tags=["games"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
