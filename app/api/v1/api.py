from fastapi import APIRouter
from app.api.v1.endpoints import health, automation

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(automation.router, prefix="/automation", tags=["Automatización"])
