from fastapi import APIRouter

from app.api.routers import games, players, teams, system, actions, techs, subtechs, updates, exercises, algorithm, auth

api_router = APIRouter()
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(games.router, prefix="/games", tags=["games"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(actions.router, prefix="/actions", tags=["actions"])
api_router.include_router(techs.router, prefix="/techs", tags=["techs"])
api_router.include_router(subtechs.router, prefix="/subtechs", tags=["subtechs"])
api_router.include_router(updates.router, prefix="/updates", tags=["updates"])
api_router.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
api_router.include_router(algorithm.router, prefix="/algorithm", tags=["algorithm"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])