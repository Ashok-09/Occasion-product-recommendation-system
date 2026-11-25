"""FastAPI entry point and application lifecycle setup."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.data_loader import CatalogLoadError, load_and_preprocess_catalog
from app.recommender import OccasionRecommender
from app.routes import router as api_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(custom_settings: Settings | None = None) -> FastAPI:
    """Application factory so tests and runtime share identical startup wiring."""
    active_settings = custom_settings or get_settings()

    @asynccontextmanager
    async def lifespan(app_instance: FastAPI):
        app_instance.state.settings = active_settings
        app_instance.state.catalog = None
        app_instance.state.recommender = None
        app_instance.state.load_error = None

        try:
            loaded = load_and_preprocess_catalog(active_settings.catalog_path)
            app_instance.state.catalog = loaded
            app_instance.state.recommender = OccasionRecommender(
                loaded.products,
                active_settings.recommendation,
            )
            logger.info(
                "Backend ready with %d eligible products.",
                loaded.stats.eligible_records,
            )
        except CatalogLoadError as exc:
            app_instance.state.load_error = str(exc)
            logger.error("Catalog initialization failed: %s", exc)

        yield

    application = FastAPI(
        title=active_settings.app_name,
        version="1.0.0",
        description="Recommends catalog products tailored to a user-entered occasion.",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(active_settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router)
    return application


app = create_app()
