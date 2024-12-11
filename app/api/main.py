from fastapi import APIRouter

from app.api.routers import games, players, teams

api_router = APIRouter()
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
