from fastapi import APIRouter

from app.api.v1.agents import router as agents_router
from app.api.v1.auth import router as auth_router
from app.api.v1.prompts import router as prompts_router
from app.api.v1.templates import router as templates_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(templates_router, prefix="/templates", tags=["templates"])
api_router.include_router(prompts_router, prefix="/prompts", tags=["prompts"])


@api_router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent-builder"}
