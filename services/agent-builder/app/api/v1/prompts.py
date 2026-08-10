from fastapi import APIRouter, Depends, HTTPException, status
from shared.auth.roles import Role
from shared.models.prompt import PromptVersion

from app.core.security import get_current_active_user, require_role
from app.models.user import User
from app.schemas.prompt import PromptCreate, PromptVersionCreate
from app.services import prompts as prompts_service

router = APIRouter()

can_write = require_role(Role.ADMIN, Role.DEVELOPER)


@router.post("", response_model=PromptVersion, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    payload: PromptCreate,
    user: User = Depends(can_write),
) -> PromptVersion:
    return await prompts_service.create_prompt(
        tenant_id=user.tenant_id, created_by=str(user.id), payload=payload
    )


@router.get("", response_model=list[PromptVersion])
async def list_prompts(
    user: User = Depends(get_current_active_user),
) -> list[PromptVersion]:
    return await prompts_service.list_prompts(user.tenant_id)


@router.get("/{prompt_id}/versions", response_model=list[PromptVersion])
async def list_versions(
    prompt_id: str,
    user: User = Depends(get_current_active_user),
) -> list[PromptVersion]:
    versions = await prompts_service.list_versions(user.tenant_id, prompt_id)
    if not versions:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Prompt not found")
    return versions


@router.post(
    "/{prompt_id}/versions", response_model=PromptVersion, status_code=status.HTTP_201_CREATED
)
async def create_version(
    prompt_id: str,
    payload: PromptVersionCreate,
    user: User = Depends(can_write),
) -> PromptVersion:
    version = await prompts_service.create_version(user.tenant_id, prompt_id, str(user.id), payload)
    if version is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Prompt not found")
    return version
