from fastapi import APIRouter, Depends, HTTPException, status
from shared.models.template import TemplateConfig

from app.core.security import get_current_active_user
from app.services import templates as templates_service

router = APIRouter()


@router.get("", response_model=list[TemplateConfig])
async def list_templates(
    category: str | None = None,
    _user=Depends(get_current_active_user),
) -> list[TemplateConfig]:
    return await templates_service.list_templates(category)


@router.get("/{template_id}", response_model=TemplateConfig)
async def get_template(
    template_id: str,
    _user=Depends(get_current_active_user),
) -> TemplateConfig:
    template = await templates_service.get_template(template_id)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")
    return template
