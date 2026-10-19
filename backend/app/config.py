"""Application configuration loaded from environment / .env file.

Fails loudly with a clear message when required settings (GEMINI_API_KEY) are missing.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the repository root (backend/app/config.py -> parents[2] == repo root)
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Typed application settings, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=str(_REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM -----------------------------------------------------------------
    gemini_api_key: str = Field(
        ...,
        description="Google Gemini API key. Required — the app fails fast without it.",
    )
    gemini_model: str = Field("gemini-1.5-flash", description="Gemini model id")

    # --- Database --------------------------------------------------------------
    database_url: str = Field(
        "sqlite+aiosqlite:///./multivisions.db",
        description="SQLAlchemy async database URL",
    )
    data_dir: Path = Field(
        _REPO_ROOT / "data",
        description="Directory holding company.json / products.json / pricing.json",
    )

    # --- API -------------------------------------------------------------------
    backend_cors_origins: str = Field(
        "http://localhost:3000",
        description="Comma-separated list of allowed CORS origins",
    )

    @field_validator("gemini_api_key")
    @classmethod
    def _require_api_key(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError(
                "GEMINI_API_KEY is missing. Create a .env file (see .env.example) "
                "and set GEMINI_API_KEY=your-key. The app cannot start without it."
            )
        return v

    @field_validator("data_dir")
    @classmethod
    def _ensure_data_dir(cls, v: Path) -> Path:
        # Resolve relative DATA_DIR against the repo root (not the CWD) so the
        # seed JSON files are found regardless of where uvicorn is launched from.
        if not v.is_absolute():
            v = _REPO_ROOT / v
        v.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


settings = get_settings()
