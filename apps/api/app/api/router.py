from fastapi import APIRouter

from app.api import catalog, health, me, power, practice, progress, retrieval, tutor

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(me.router)
api_router.include_router(catalog.router)
api_router.include_router(power.router)
api_router.include_router(tutor.router)
api_router.include_router(practice.router)
api_router.include_router(progress.router)
api_router.include_router(retrieval.router)
