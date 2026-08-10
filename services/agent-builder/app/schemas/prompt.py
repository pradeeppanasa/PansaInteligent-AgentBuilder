from pydantic import BaseModel, Field


class PromptCreate(BaseModel):
    name: str
    content: str
    variables: list[str] = Field(default_factory=list)


class PromptVersionCreate(BaseModel):
    content: str
    name: str | None = None
    variables: list[str] | None = None
