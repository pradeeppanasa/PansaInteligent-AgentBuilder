from fastapi import APIRouter

from app.api.v1.auth import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])


@api_router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent-builder"}
