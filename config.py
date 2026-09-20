from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "IT Helping Agent"
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "qwen3.5:latest"
    ollama_timeout_seconds: float = 180.0
    agent_max_parallel: int = 2
    data_dir: Path = Path("data")
    prompt_dir: Path = Path("prompts")
    skills_dir: Path = Path("skills")
    knowledge_dir: Path = Path("knowledge")
    log_level: str = "INFO"
    rag_top_k: int = 4
    max_history_items: int = 3
    allow_high_risk_actions: bool = False
    otel_exporter_otlp_endpoint: str = "http://jaeger:4318"
    otel_enabled: bool = True

    @property
    def database_path(self) -> Path:
        return self.data_dir / "helping.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
