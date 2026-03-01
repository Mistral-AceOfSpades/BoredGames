"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings with environment variable binding."""

    # App
    app_name: str = "BoredGames API"
    debug: bool = False
    secret_key: str
    enable_dev_token: bool = False
    oauth_state_ttl_seconds: int = 600
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
        "https://mistral-aceofspades.github.io",
    ]

    # Mistral AI
    mistral_api_key: str = ""

    # Mistral Models
    model_ocr: str = "mistral-ocr-2512"
    model_large: str = "mistral-large-2512"
    model_schema_ft: str = "ft:mistral-small-3-2-2506:boredgames-schema-v1"
    model_qa_ft: str = "ft:mistral-small-3-2-2506:boredgames-qa-v1"
    model_houserules_ft: str = "ft:mistral-small-3-2-2506:boredgames-houserules-v1"
    model_reasoning: str = "magistral-medium-2509"
    model_voice: str = "voxtral-mini-transcribe-2-2602"
    model_embed: str = "mistral-embed"
    model_moderation: str = "mistral-moderation-2411"

    # Database
    database_url: str = "sqlite+aiosqlite:///./boredgames.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    github_client_id: str = ""
    github_client_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440  # 24 hours

    # Storage
    r2_endpoint: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_bucket: str = "boredgames-uploads"

    model_config = {
        "env_file": os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "env_prefix": "",
        "alias_generator": None,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.secret_key in {"change-me-in-production", "dev-secret-change-in-production"}:
            raise ValueError("SECRET_KEY must be set to a non-placeholder value")

        # Map the .env key name to our field
        if not self.mistral_api_key:
            from dotenv import dotenv_values

            env_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), ".env"
            )
            values = dotenv_values(env_path)
            if "MistralAPIKey" in values:
                self.mistral_api_key = values["MistralAPIKey"].strip("'\"")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
