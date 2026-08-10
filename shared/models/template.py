from pydantic import BaseModel, Field

from shared.models.agent import GuardrailConfig, ModelConfig


class TemplateConfig(BaseModel):
    template_id: str
    category: str
    name: str
    description: str
    default_system_prompt: str
    suggested_tools: list[str] = Field(default_factory=list)
    suggested_model: ModelConfig
    guardrail_preset: GuardrailConfig
