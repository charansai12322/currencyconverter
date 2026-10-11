"""Application configuration module."""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    API_TIMEOUT_SECONDS: float = 15.0
    CACHE_TTL_SECONDS: int = 3600
    GEMINI_API_KEY: Optional[str] = None

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated origin strings into a cleaned list."""
        if not self.CORS_ALLOWED_ORIGINS:
            return []
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
