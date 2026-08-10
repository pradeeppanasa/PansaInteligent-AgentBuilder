import asyncio

from shared.models.agent import GuardrailConfig, ModelConfig
from shared.models.template import TemplateConfig

from app.core.dynamodb import get_templates_table, to_dynamo_item

DEFAULT_TEMPLATES = [
    TemplateConfig(
        template_id="customer-support-v1",
        category="customer-support",
        name="Customer Support Agent",
        description="Handles customer inquiries, troubleshooting, and support tickets.",
        default_system_prompt=(
            "You are a helpful, empathetic customer support agent. Answer customer questions "
            "accurately, escalate issues you cannot resolve, and always maintain a professional "
            "and friendly tone."
        ),
        suggested_tools=["knowledge_base_search", "create_ticket"],
        suggested_model=ModelConfig(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"),
        guardrail_preset=GuardrailConfig(pii_action="redact", toxicity_threshold=0.3),
    ),
    TemplateConfig(
        template_id="data-analyst-v1",
        category="data-analysis",
        name="Data Analyst Agent",
        description="Analyzes datasets, generates insights, and answers data questions.",
        default_system_prompt=(
            "You are a meticulous data analyst. Use the available tools to query data, perform "
            "calculations, and present findings clearly with supporting evidence."
        ),
        suggested_tools=["sql_query", "chart_generator"],
        suggested_model=ModelConfig(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"),
        guardrail_preset=GuardrailConfig(pii_action="redact", max_output_tokens=4096),
    ),
    TemplateConfig(
        template_id="code-review-v1",
        category="engineering",
        name="Code Review Agent",
        description="Reviews code changes for bugs, style issues, and best practices.",
        default_system_prompt=(
            "You are a senior software engineer performing code review. Identify bugs, security "
            "issues, and style violations. Be constructive and specific."
        ),
        suggested_tools=["read_file", "run_linter"],
        suggested_model=ModelConfig(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"),
        guardrail_preset=GuardrailConfig(pii_action="allow", injection_detection=True),
    ),
    TemplateConfig(
        template_id="document-qa-v1",
        category="knowledge",
        name="Document Q&A Agent",
        description="Answers questions grounded in a specific document knowledge base.",
        default_system_prompt=(
            "You are a document Q&A assistant. Only answer using information found in the "
            "provided knowledge base. If the answer isn't in the documents, say so."
        ),
        suggested_tools=["knowledge_base_search"],
        suggested_model=ModelConfig(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"),
        guardrail_preset=GuardrailConfig(pii_action="redact"),
    ),
    TemplateConfig(
        template_id="hr-assistant-v1",
        category="hr",
        name="HR Assistant",
        description="Answers employee questions about HR policies, benefits, and leave.",
        default_system_prompt=(
            "You are an HR assistant. Answer employee questions about company policies, "
            "benefits, and leave using the HR knowledge base. Do not disclose confidential "
            "information about other employees."
        ),
        suggested_tools=["knowledge_base_search"],
        suggested_model=ModelConfig(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"),
        guardrail_preset=GuardrailConfig(pii_action="block", toxicity_threshold=0.3),
    ),
]


def seed_default_templates_sync() -> None:
    table = get_templates_table()
    for template in DEFAULT_TEMPLATES:
        table.put_item(Item=to_dynamo_item(template.model_dump(mode="json")))


async def seed_default_templates() -> None:
    await asyncio.to_thread(seed_default_templates_sync)
