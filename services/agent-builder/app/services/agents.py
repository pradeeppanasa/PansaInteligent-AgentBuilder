import asyncio
import base64
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from boto3.dynamodb.conditions import Key
from shared.models.agent import AgentConfig

from app.core.dynamodb import get_agents_table, to_dynamo_item
from app.schemas.agent import AgentCreate, AgentUpdate


def _encode_cursor(key: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(key).encode()).decode()


def _decode_cursor(cursor: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())


async def create_agent(*, tenant_id: str, created_by: str, payload: AgentCreate) -> AgentConfig:
    now = datetime.now(UTC)
    agent = AgentConfig(
        agent_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
        template_id=payload.template_id,
        system_prompt=payload.system_prompt,
        tools=payload.tools,
        llm_config=payload.llm_config,
        guardrail_config=payload.guardrail_config,
        kb_config=payload.kb_config,
        created_by=created_by,
        created_at=now,
        updated_at=now,
        status="draft",
    )
    item = to_dynamo_item(agent.model_dump(mode="json", by_alias=True))
    table = get_agents_table()
    await asyncio.to_thread(table.put_item, Item=item)
    return agent


async def get_agent(tenant_id: str, agent_id: str) -> AgentConfig | None:
    table = get_agents_table()
    response = await asyncio.to_thread(
        table.get_item, Key={"tenant_id": tenant_id, "agent_id": agent_id}
    )
    item = response.get("Item")
    return AgentConfig.model_validate(item) if item else None


async def list_agents(
    *, tenant_id: str, limit: int, cursor: str | None
) -> tuple[list[AgentConfig], str | None]:
    table = get_agents_table()
    kwargs: dict[str, Any] = {
        "KeyConditionExpression": Key("tenant_id").eq(tenant_id),
        "Limit": limit,
    }
    if cursor:
        kwargs["ExclusiveStartKey"] = _decode_cursor(cursor)

    response = await asyncio.to_thread(table.query, **kwargs)
    items = [AgentConfig.model_validate(item) for item in response.get("Items", [])]
    last_key = response.get("LastEvaluatedKey")
    next_cursor = _encode_cursor(last_key) if last_key else None
    return items, next_cursor


async def update_agent(tenant_id: str, agent_id: str, payload: AgentUpdate) -> AgentConfig | None:
    existing = await get_agent(tenant_id, agent_id)
    if existing is None:
        return None

    updated = existing.model_copy(update=payload.model_dump(exclude_unset=True))
    updated.updated_at = datetime.now(UTC)

    item = to_dynamo_item(updated.model_dump(mode="json", by_alias=True))
    table = get_agents_table()
    await asyncio.to_thread(table.put_item, Item=item)
    return updated


async def delete_agent(tenant_id: str, agent_id: str) -> bool:
    existing = await get_agent(tenant_id, agent_id)
    if existing is None:
        return False
    table = get_agents_table()
    await asyncio.to_thread(table.delete_item, Key={"tenant_id": tenant_id, "agent_id": agent_id})
    return True


async def duplicate_agent(tenant_id: str, agent_id: str, created_by: str) -> AgentConfig | None:
    existing = await get_agent(tenant_id, agent_id)
    if existing is None:
        return None

    now = datetime.now(UTC)
    duplicate = existing.model_copy(
        update={
            "agent_id": str(uuid.uuid4()),
            "name": f"{existing.name} (copy)",
            "created_by": created_by,
            "created_at": now,
            "updated_at": now,
            "status": "draft",
        }
    )
    item = to_dynamo_item(duplicate.model_dump(mode="json", by_alias=True))
    table = get_agents_table()
    await asyncio.to_thread(table.put_item, Item=item)
    return duplicate
