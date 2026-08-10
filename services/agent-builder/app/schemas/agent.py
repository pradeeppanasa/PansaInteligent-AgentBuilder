from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from shared.models.agent import AgentConfig, GuardrailConfig, KBConfig, ModelConfig


class AgentCreate(BaseModel):
    name: str
    description: str
    template_id: str | None = None
    system_prompt: str
    tools: list[str] = Field(default_factory=list)
    llm_config: ModelConfig = Field(alias="model_config", serialization_alias="model_config")
    guardrail_config: GuardrailConfig
    kb_config: KBConfig | None = None

    model_config = ConfigDict(populate_by_name=True)


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    template_id: str | None = None
    system_prompt: str | None = None
    tools: list[str] | None = None
    llm_config: ModelConfig | None = Field(
        default=None, alias="model_config", serialization_alias="model_config"
    )
    guardrail_config: GuardrailConfig | None = None
    kb_config: KBConfig | None = None
    status: Literal["draft", "active", "archived"] | None = None

    model_config = ConfigDict(populate_by_name=True)


class AgentListResponse(BaseModel):
    items: list[AgentConfig]
    next_cursor: str | None = None
