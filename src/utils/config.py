"""Configuration management using pydantic-settings."""
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Notion API
    notion_api_key: str = Field(..., description="Notion integration token")
    notion_workspace_id: str = Field(default="", description="Notion workspace ID")

    # Anthropic Claude API
    anthropic_api_key: str = Field(..., description="Anthropic API key")

    # LangSmith (Optional)
    langchain_tracing_v2: bool = Field(default=False)
    langchain_api_key: str = Field(default="")
    langchain_project: str = Field(default="notion-knowledge-agent")

    # Vector Database
    vector_db_path: Path = Field(default=Path("./data/vector_db"))
    vector_db_type: Literal["chromadb", "faiss"] = Field(default="chromadb")

    # Embedding Model
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")

    # Sync Schedule
    sync_hour: int = Field(default=4, ge=0, le=23)
    sync_timezone: str = Field(default="Asia/Seoul")

    # Application
    log_level: str = Field(default="INFO")
    environment: Literal["development", "production"] = Field(default="development")

    # Paths
    @property
    def data_dir(self) -> Path:
        return Path("./data")

    @property
    def profiles_dir(self) -> Path:
        return self.data_dir / "profiles"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    def model_post_init(self, __context):
        """Create directories if they don't exist."""
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
