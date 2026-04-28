"""Application settings (environment-driven)."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment."""

    model_config = SettingsConfigDict(
        env_prefix="ASC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_token: str = Field(
        default="change-me",
        description="Bearer token for API (set ASC_API_TOKEN in production).",
    )
    data_dir: Path = Field(default=Path("./data"))
    database_url: str = Field(
        default="sqlite:///./data/events.db",
        description="Reserved for future SQLAlchemy; SQLite path derived from data_dir.",
    )

    @property
    def sqlite_path(self) -> Path:
        """Primary SQLite file for event metadata."""
        return self.data_dir / "events.db"

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llava"
    ntfy_topic_url: str | None = None
    go2rtc_api_url: str | None = Field(
        default=None,
        description="Optional go2rtc HTTP API base for stream status.",
    )


def get_settings() -> Settings:
    """Factory for FastAPI dependency injection."""
    return Settings()
