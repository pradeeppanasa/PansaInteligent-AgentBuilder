from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

_resource = None


def to_dynamo_item(value: Any) -> Any:
    """Recursively convert floats to Decimal, as required by the DynamoDB resource API."""
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: to_dynamo_item(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_dynamo_item(v) for v in value]
    return value


def get_dynamodb_resource():
    global _resource
    if _resource is None:
        kwargs = {"region_name": settings.AWS_REGION}
        if settings.DYNAMODB_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.DYNAMODB_ENDPOINT_URL
        if settings.AWS_ACCESS_KEY_ID:
            kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        _resource = boto3.resource("dynamodb", **kwargs)
    return _resource


def get_agents_table():
    return get_dynamodb_resource().Table(settings.DYNAMODB_TABLE_AGENTS)


def get_templates_table():
    return get_dynamodb_resource().Table(settings.DYNAMODB_TABLE_TEMPLATES)


def _create_table_if_not_exists(*, table_name: str, hash_key: str, range_key: str) -> None:
    """Idempotently create a table for local/dev use.

    In deployed environments tables are provisioned by Terraform instead.
    """
    resource = get_dynamodb_resource()
    try:
        resource.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": hash_key, "KeyType": "HASH"},
                {"AttributeName": range_key, "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": hash_key, "AttributeType": "S"},
                {"AttributeName": range_key, "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        ).wait_until_exists()
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceInUseException":
            raise


def ensure_agents_table() -> None:
    _create_table_if_not_exists(
        table_name=settings.DYNAMODB_TABLE_AGENTS, hash_key="tenant_id", range_key="agent_id"
    )


def ensure_templates_table() -> None:
    _create_table_if_not_exists(
        table_name=settings.DYNAMODB_TABLE_TEMPLATES, hash_key="category", range_key="template_id"
    )
