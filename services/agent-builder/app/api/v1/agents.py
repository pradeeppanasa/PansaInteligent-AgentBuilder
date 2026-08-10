from fastapi import APIRouter, Depends, HTTPException, Query, status
from shared.auth.roles import Role
from shared.models.agent import AgentConfig

from app.core.security import get_current_active_user, require_role
from app.models.user import User
from app.schemas.agent import AgentCreate, AgentListResponse, AgentUpdate
from app.services import agents as agents_service
from app.services import templates as templates_service

router = APIRouter()

can_write = require_role(Role.ADMIN, Role.DEVELOPER)


@router.post("", response_model=AgentConfig, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate,
    user: User = Depends(can_write),
) -> AgentConfig:
    return await agents_service.create_agent(
        tenant_id=user.tenant_id, created_by=str(user.id), payload=payload
    )


@router.get("", response_model=AgentListResponse)
async def list_agents(
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
    user: User = Depends(get_current_active_user),
) -> AgentListResponse:
    items, next_cursor = await agents_service.list_agents(
        tenant_id=user.tenant_id, limit=limit, cursor=cursor
    )
    return AgentListResponse(items=items, next_cursor=next_cursor)


@router.get("/{agent_id}", response_model=AgentConfig)
async def get_agent(
    agent_id: str,
    user: User = Depends(get_current_active_user),
) -> AgentConfig:
    agent = await agents_service.get_agent(user.tenant_id, agent_id)
    if agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentConfig)
async def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    user: User = Depends(can_write),
) -> AgentConfig:
    agent = await agents_service.update_agent(user.tenant_id, agent_id, payload)
    if agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent not found")
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    user: User = Depends(can_write),
) -> None:
    deleted = await agents_service.delete_agent(user.tenant_id, agent_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent not found")


@router.post(
    "/from-template/{template_id}", response_model=AgentConfig, status_code=status.HTTP_201_CREATED
)
async def create_agent_from_template(
    template_id: str,
    user: User = Depends(can_write),
) -> AgentConfig:
    template = await templates_service.get_template(template_id)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

    payload = AgentCreate(
        name=template.name,
        description=template.description,
        template_id=template.template_id,
        system_prompt=template.default_system_prompt,
        tools=template.suggested_tools,
        llm_config=template.suggested_model,
        guardrail_config=template.guardrail_preset,
    )
    return await agents_service.create_agent(
        tenant_id=user.tenant_id, created_by=str(user.id), payload=payload
    )


@router.post(
    "/{agent_id}/duplicate", response_model=AgentConfig, status_code=status.HTTP_201_CREATED
)
async def duplicate_agent(
    agent_id: str,
    user: User = Depends(can_write),
) -> AgentConfig:
    agent = await agents_service.duplicate_agent(user.tenant_id, agent_id, created_by=str(user.id))
    if agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent not found")
    return agent
