import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "donata-ia-api"
    env: str = "dev"
    log_level: str = "INFO"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "donata_ia"
    mongo_db_test: str = "donata_ia_test"

    jwt_secret: str = secrets.token_urlsafe(64)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    enable_local_login: bool = True
    local_admin_username: str = "admin"
    local_admin_password: str = "cambiar-esta-clave"

    cors_origins: list[str] = ["http://localhost:5173"]

    rate_limit_enabled: bool = True
    rate_limit_login: int = 10
    rate_limit_chat: int = 20
    rate_limit_export: int = 10
    rate_limit_write: int = 60
    rate_limit_global: int = 120

    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "qwen2.5:7b-instruct"
    ollama_temperature: float = 0.1
    ollama_top_p: float = 0.95
    ollama_max_tokens: int = 2048
    ollama_timeout: float = 60.0

    chroma_dir: str = "data/chroma"
    embedding_provider: str = "huggingface"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    rag_top_k: int = 4

    chat_history_limit: int = 20
    llm_use_mcp: bool = True
    guardrails_enabled: bool = True

    vite_api_url: str = "http://localhost:8000"

    @property
    def cors_origins_list(self) -> list[str]:
        return self.cors_origins


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
