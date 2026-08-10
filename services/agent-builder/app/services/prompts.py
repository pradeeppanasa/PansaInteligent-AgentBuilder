import asyncio
import uuid
from datetime import UTC, datetime

from boto3.dynamodb.conditions import Key
from shared.models.prompt import PromptVersion

from app.core.dynamodb import get_prompts_table, to_dynamo_item
from app.schemas.prompt import PromptCreate, PromptVersionCreate


def _sort_key(prompt_id: str, version: int) -> str:
    return f"{prompt_id}#{version:06d}"


async def _put_version(version: PromptVersion) -> None:
    table = get_prompts_table()
    item = to_dynamo_item(version.model_dump(mode="json"))
    item["sort_key"] = _sort_key(version.prompt_id, version.version)
    await asyncio.to_thread(table.put_item, Item=item)


async def create_prompt(*, tenant_id: str, created_by: str, payload: PromptCreate) -> PromptVersion:
    version = PromptVersion(
        prompt_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        version=1,
        name=payload.name,
        content=payload.content,
        variables=payload.variables,
        created_by=created_by,
        created_at=datetime.now(UTC),
    )
    await _put_version(version)
    return version


async def list_prompts(tenant_id: str) -> list[PromptVersion]:
    table = get_prompts_table()
    response = await asyncio.to_thread(
        table.query, KeyConditionExpression=Key("tenant_id").eq(tenant_id)
    )
    latest_by_prompt: dict[str, PromptVersion] = {}
    for item in response.get("Items", []):
        version = PromptVersion.model_validate(item)
        existing = latest_by_prompt.get(version.prompt_id)
        if existing is None or version.version > existing.version:
            latest_by_prompt[version.prompt_id] = version
    return sorted(latest_by_prompt.values(), key=lambda v: v.created_at)


async def list_versions(tenant_id: str, prompt_id: str) -> list[PromptVersion]:
    table = get_prompts_table()
    response = await asyncio.to_thread(
        table.query,
        KeyConditionExpression=(
            Key("tenant_id").eq(tenant_id) & Key("sort_key").begins_with(f"{prompt_id}#")
        ),
    )
    items = [PromptVersion.model_validate(item) for item in response.get("Items", [])]
    return sorted(items, key=lambda v: v.version)


async def create_version(
    tenant_id: str, prompt_id: str, created_by: str, payload: PromptVersionCreate
) -> PromptVersion | None:
    versions = await list_versions(tenant_id, prompt_id)
    if not versions:
        return None

    latest = versions[-1]
    new_version = PromptVersion(
        prompt_id=prompt_id,
        tenant_id=tenant_id,
        version=latest.version + 1,
        name=payload.name if payload.name is not None else latest.name,
        content=payload.content,
        variables=payload.variables if payload.variables is not None else latest.variables,
        created_by=created_by,
        created_at=datetime.now(UTC),
    )
    await _put_version(new_version)
    return new_version
