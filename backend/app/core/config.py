from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_env_file() -> str:
    candidates = [
        Path(__file__).resolve().parents[1] / ".env",
        Path(__file__).resolve().parents[2] / ".env",
        Path.cwd() / ".env",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(Path(__file__).resolve().parents[1] / ".env")


class Settings(BaseSettings):
    app_name: str = "MyDesk AI"
    environment: str = "development"
    debug: bool = False
    database_url: str = "sqlite:///./app.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    cors_origins: str = "http://localhost:3000"
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    llm_provider: str = "groq"
    groq_api_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/oauth/google/callback"

    # DB pool settings
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Production safety defaults
    required_envs: list[str] = ["DATABASE_URL", "JWT_SECRET"]

    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        if isinstance(self.cors_origins, str):
            stripped = self.cors_origins.strip()
            if not stripped:
                return ["http://localhost:3000"]
            if stripped.startswith("["):
                stripped = stripped.strip("[]")
            return [item.strip() for item in stripped.split(",") if item.strip()]
        if isinstance(self.cors_origins, list):
            return self.cors_origins
        return [str(self.cors_origins)]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def validate_required_settings() -> None:
    """Validate required settings for production readiness and fail fast.

    Call this during application startup to ensure required secrets and urls
    are present when running in production.
    """
    missing: list[str] = []
    # If environment is production, require JWT_SECRET and DATABASE_URL
    env = settings.environment.lower() if settings.environment else ""
    if env == "production":
        if not settings.jwt_secret:
            missing.append("JWT_SECRET")
        if not settings.database_url or settings.database_url.startswith("sqlite"):
            missing.append("DATABASE_URL (must be Postgres or compatible)")
    # Always require database_url
    if not settings.database_url:
        missing.append("DATABASE_URL")
    if missing:
        raise RuntimeError(f"Missing required environment settings: {', '.join(missing)}")
