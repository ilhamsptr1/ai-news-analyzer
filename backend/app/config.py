"""
AI News Analyzer — Backend Configuration
Uses pydantic-settings to load from environment variables / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_name: str = "AI News Analyzer"
    app_env: str = "development"
    app_version: str = "1.0.0"

    # Server
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    # CORS — comma-separated allowed origins
    frontend_url: str = "http://localhost:5173"

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_news_analyzer"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        """Return list of allowed CORS origins."""
        return [origin.strip() for origin in self.frontend_url.split(",")]


# Singleton — import this everywhere
settings = Settings()
