"""Application configuration loaded from environment variables with safe defaults."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


# Resolve key directories once so paths work regardless of where uvicorn is launched.
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")


def _resolve_catalog_path(raw_path: str) -> Path:
    """Resolve a relative catalog path against the backend directory."""
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (BACKEND_DIR / candidate).resolve()


@dataclass(frozen=True)
class RecommendationConfig:
    """Weights and thresholds controlling the hybrid recommendation scoring pipeline."""

    tfidf_weight: float = 0.45
    title_weight: float = 0.25
    description_weight: float = 0.30
    placeholder_penalty: float = 0.35
    min_score_threshold: float = 0.15
    default_top_k: int = 12


@dataclass(frozen=True)
class Settings:
    """Immutable settings container for the backend service."""

    app_name: str
    app_env: str
    host: str
    port: int
    catalog_path: Path
    cors_origins: tuple[str, ...]
    recommendation: RecommendationConfig = RecommendationConfig()


def get_settings() -> Settings:
    """Build settings from environment variables or local development defaults."""
    raw_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    origins = tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())

    return Settings(
        app_name=os.getenv("APP_NAME", "Occasion-Based Product Recommendation System"),
        app_env=os.getenv("APP_ENV", "development"),
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        catalog_path=_resolve_catalog_path(os.getenv("CATALOG_PATH", "../data/products.json")),
        cors_origins=origins,
    )
