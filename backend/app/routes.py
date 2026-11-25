"""REST API endpoints for health, catalog inspection, occasion suggestions, and recommendations."""

import logging

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.data_loader import LoadedCatalog
from app.recommender import OccasionRecommender
from app.schemas import (
    CatalogProductDTO,
    CatalogProductsResponse,
    HealthResponse,
    OccasionsResponse,
    ProductRecord,
    RecommendRequest,
    RecommendResponse,
    RecommendedProductDTO,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Recommendations"])


def _get_engine_state(request: Request) -> tuple[LoadedCatalog, OccasionRecommender]:
    """Retrieve initialized catalog and recommender from app state or fail cleanly with 503."""
    catalog: LoadedCatalog | None = getattr(request.app.state, "catalog", None)
    recommender: OccasionRecommender | None = getattr(request.app.state, "recommender", None)
    load_error: str | None = getattr(request.app.state, "load_error", None)

    if catalog is None or recommender is None:
        detail = load_error or "Product catalog is not ready."
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
    return catalog, recommender


def _to_catalog_dto(product: ProductRecord) -> CatalogProductDTO:
    """Convert internal ProductRecord to public catalog API representation."""
    return CatalogProductDTO(
        product_id=product.product_id,
        vendor_id=product.vendor_id,
        category_id=product.category_id,
        name=product.name,
        brand=product.brand,
        description=product.description,
        image=product.image,
        files=product.files,
        price=product.price,
        discount_percentage=product.discount_percentage,
        discounted_price=product.discounted_price,
        stock=product.stock,
    )


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check(request: Request) -> HealthResponse:
    """Return service health along with raw vs. eligible catalog counts."""
    settings = request.app.state.settings
    catalog: LoadedCatalog | None = getattr(request.app.state, "catalog", None)
    load_error: str | None = getattr(request.app.state, "load_error", None)

    if catalog is None:
        return HealthResponse(
            status="degraded" if load_error else "starting",
            environment=settings.app_env,
            catalog_found=settings.catalog_path.is_file(),
            total_raw_products=0,
            eligible_products=0,
            excluded_products=0,
        )

    return HealthResponse(
        status="ok",
        environment=settings.app_env,
        catalog_found=True,
        total_raw_products=catalog.stats.total_records,
        eligible_products=catalog.stats.eligible_records,
        excluded_products=catalog.stats.excluded_records,
    )


@router.get("/occasions", response_model=OccasionsResponse)
def get_suggested_occasions() -> OccasionsResponse:
    """Return suggested occasions supported by the recommendation engine."""
    return OccasionsResponse(occasions=OccasionRecommender.list_supported_occasions())


@router.get("/products", response_model=CatalogProductsResponse)
def list_eligible_products(
    request: Request,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> CatalogProductsResponse:
    """Return paginated eligible products from the preprocessed catalog."""
    catalog, _ = _get_engine_state(request)
    sliced = catalog.products[offset : offset + limit]
    return CatalogProductsResponse(
        total_eligible=len(catalog.products),
        limit=limit,
        offset=offset,
        products=[_to_catalog_dto(item) for item in sliced],
    )


@router.post("/recommend", response_model=RecommendResponse)
def recommend_products(request: Request, payload: RecommendRequest) -> RecommendResponse:
    """Score and rank eligible catalog products for the requested occasion."""
    _, recommender = _get_engine_state(request)
    scored = recommender.recommend(payload.occasion, top_k=payload.top_k)

    logger.info(
        "Occasion recommendation query=%r returned=%d results",
        payload.occasion,
        len(scored),
    )

    items = [
        RecommendedProductDTO(
            product_id=entry.product.product_id,
            vendor_id=entry.product.vendor_id,
            category_id=entry.product.category_id,
            name=entry.product.name,
            brand=entry.product.brand,
            description=entry.product.description,
            image=entry.product.image,
            files=entry.product.files,
            price=entry.product.price,
            discount_percentage=entry.product.discount_percentage,
            discounted_price=entry.product.discounted_price,
            stock=entry.product.stock,
            score=entry.score,
            reason=entry.reason,
        )
        for entry in scored
    ]

    if not items:
        message = (
            f"No strong matches found for '{payload.occasion}'. "
            "Try occasions like Birthday, Wedding, Diwali, Valentine's Day, or Office Party."
        )
    else:
        message = f"Found {len(items)} recommended products for '{payload.occasion}'."

    return RecommendResponse(
        occasion=payload.occasion,
        total_results=len(items),
        recommendations=items,
        message=message,
    )
