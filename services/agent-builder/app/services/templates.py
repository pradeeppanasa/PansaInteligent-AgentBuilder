import asyncio

from boto3.dynamodb.conditions import Attr, Key
from shared.models.template import TemplateConfig

from app.core.dynamodb import get_templates_table


async def list_templates(category: str | None = None) -> list[TemplateConfig]:
    table = get_templates_table()
    if category:
        response = await asyncio.to_thread(
            table.query, KeyConditionExpression=Key("category").eq(category)
        )
    else:
        # Global catalog, small and slow-growing - a full scan is fine here.
        response = await asyncio.to_thread(table.scan)
    return [TemplateConfig.model_validate(item) for item in response.get("Items", [])]


async def get_template(template_id: str) -> TemplateConfig | None:
    table = get_templates_table()
    response = await asyncio.to_thread(
        table.scan, FilterExpression=Attr("template_id").eq(template_id)
    )
    items = response.get("Items", [])
    return TemplateConfig.model_validate(items[0]) if items else None
