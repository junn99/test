"""Application settings and configuration."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application Settings
    app_name: str = "Email Assistant Agent"
    app_version: str = "1.0.0"
    debug: bool = False

    # LLM Settings
    llm_provider: str = "openai"  # openai, anthropic
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.7
    max_tokens: int = 2000

    # Gmail API Settings
    gmail_credentials_file: str = "credentials.json"
    gmail_token_file: str = "token.json"
    gmail_scopes: list[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.modify"
    ]

    # Outlook Settings (Optional)
    outlook_client_id: Optional[str] = None
    outlook_client_secret: Optional[str] = None
    outlook_tenant_id: Optional[str] = None

    # Email Settings
    default_email_provider: str = "gmail"
    check_interval_seconds: int = 60
    max_emails_per_fetch: int = 50

    # Database Settings
    database_url: str = "sqlite:///./email_assistant.db"

    # Redis Settings (for caching and notifications)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    use_redis: bool = False

    # Logging
    log_level: str = "INFO"
    log_file: str = "email_assistant.log"

    # UI Settings
    streamlit_theme: str = "light"
    items_per_page: int = 20


# Global settings instance
settings = Settings()
