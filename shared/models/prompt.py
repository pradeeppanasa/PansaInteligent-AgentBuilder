from datetime import datetime

from pydantic import BaseModel, Field


class PromptVersion(BaseModel):
    prompt_id: str
    tenant_id: str
    version: int
    name: str
    content: str
    variables: list[str] = Field(default_factory=list)
    created_by: str
    created_at: datetime
