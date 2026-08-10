from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ModelConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: Literal["bedrock", "azure_openai", "self_hosted"] = "bedrock"
    model_id: str
    temperature: float = 0.7
    max_tokens: int = 2048


class GuardrailConfig(BaseModel):
    policy_id: str | None = None
    blocked_topics: list[str] = Field(default_factory=list)
    pii_action: Literal["block", "redact", "allow"] = "redact"
    injection_detection: bool = True
    toxicity_threshold: float = 0.5
    max_input_tokens: int = 4096
    max_output_tokens: int = 2048


class KBConfig(BaseModel):
    kb_id: str
    top_k: int = 5


class AgentConfig(BaseModel):
    agent_id: str
    tenant_id: str
    name: str
    description: str
    template_id: str | None = None
    system_prompt: str
    tools: list[str] = Field(default_factory=list)
    llm_config: ModelConfig = Field(alias="model_config", serialization_alias="model_config")
    guardrail_config: GuardrailConfig
    kb_config: KBConfig | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    status: Literal["draft", "active", "archived"] = "draft"

    model_config = ConfigDict(populate_by_name=True)
