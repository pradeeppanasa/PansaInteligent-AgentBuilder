import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

_resource = None


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


def ensure_agents_table() -> None:
    """Idempotently create the agents table for local/dev use.

    In deployed environments this table is provisioned by Terraform instead.
    """
    resource = get_dynamodb_resource()
    try:
        resource.create_table(
            TableName=settings.DYNAMODB_TABLE_AGENTS,
            KeySchema=[
                {"AttributeName": "tenant_id", "KeyType": "HASH"},
                {"AttributeName": "agent_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "tenant_id", "AttributeType": "S"},
                {"AttributeName": "agent_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        ).wait_until_exists()
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceInUseException":
            raise
