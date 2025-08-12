from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PR Review Agent"
    environment: str = "local"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    model_provider: str = "ollama"  # or "openai"
    openai_api_key: str | None = None
    ollama_model: str = "llama3"

    github_token_default: str | None = None

    cache_ttl_seconds: int = 3600
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    def result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


settings = Settings()  # type: ignore[call-arg]
