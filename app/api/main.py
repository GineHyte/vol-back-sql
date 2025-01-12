from fastapi import APIRouter

from app.api.routers import games, players, teams, system, actions, techs

api_router = APIRouter()
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(games.router, prefix="/games", tags=["games"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(actions.router, prefix="/actions", tags=["actions"])
api_router.include_router(techs.router, prefix="/techs", tags=["techs"])
