from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    APP_PORT: int = 8001
    SECRET_KEY: str = "changeme"

    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    DYNAMODB_ENDPOINT_URL: str | None = None

    DYNAMODB_TABLE_AGENTS: str = "panasa-agents"
    DYNAMODB_TABLE_TEMPLATES: str = "panasa-templates"
    DYNAMODB_TABLE_PROMPTS: str = "panasa-prompts"
    DYNAMODB_TABLE_SESSIONS: str = "panasa-sessions"
    DYNAMODB_TABLE_AUDIT: str = "panasa-audit"

    DATABASE_URL: str = "postgresql+asyncpg://panasa:panasa@localhost:5433/panasa_agent_builder"

    JWT_SECRET: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_MINUTES: int = 60 * 24 * 7

    BOOTSTRAP_ADMIN_EMAIL: str | None = None
    BOOTSTRAP_ADMIN_PASSWORD: str | None = None
    BOOTSTRAP_ADMIN_TENANT_ID: str = "default"

    CORS_ORIGINS: str = "http://localhost:5173"

    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_DEFAULT_MODEL: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "http://localhost:3000"

    REDIS_URL: str = "redis://localhost:6379/0"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
