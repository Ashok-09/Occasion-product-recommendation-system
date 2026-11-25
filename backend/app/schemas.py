"""Pydantic models for standardized catalog products and ingestion diagnostics."""

from pydantic import BaseModel, Field, field_validator


class ProductRecord(BaseModel):
    """Normalized product representation mapped from raw catalog JSON."""

    product_id: str
    vendor_id: str = ""
    category_id: str = ""
    name: str
    brand: str = "Unknown"
    slug: str = ""
    description: str = ""
    short_description: str = ""
    image: str | None = None
    files: list[str] = Field(default_factory=list)
    price: float | None = None
    discount_percentage: float | None = None
    discounted_price: float | None = None
    stock: int = 0
    product_group_id: str = ""
    searchable_text: str = ""
    has_placeholder_text: bool = False


class ExcludedProductInfo(BaseModel):
    """Audit details explaining why a raw product was excluded from recommendations."""

    product_id: str
    name: str
    status: str | None = None
    is_approved: bool | None = None
    reason: str


class CatalogLoadStats(BaseModel):
    """Summary metrics produced during catalog loading and preprocessing."""

    total_records: int
    eligible_records: int
    excluded_records: int
    duplicate_ids_removed: int
    duplicate_names_in_eligible: dict[str, int] = Field(default_factory=dict)
    placeholder_records_flagged: int = 0
    missing_field_counts: dict[str, int] = Field(default_factory=dict)
    excluded_details: list[ExcludedProductInfo] = Field(default_factory=list)


class LoadedCatalog(BaseModel):
    """Container holding eligible preprocessed products alongside audit statistics."""

    products: list[ProductRecord]
    stats: CatalogLoadStats


class RecommendRequest(BaseModel):
    """Request payload sent by the client when searching by occasion."""

    occasion: str = Field(..., max_length=120, description="User-entered occasion query")
    top_k: int = Field(default=12, ge=1, le=50, description="Maximum items to return")

    @field_validator("occasion")
    @classmethod
    def validate_occasion_not_blank(cls, value: str) -> str:
        """Trim surrounding whitespace and reject empty occasion strings."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Please enter an occasion before searching.")
        return cleaned


class RecommendedProductDTO(BaseModel):
    """Single recommended product serialized for API responses."""

    product_id: str
    vendor_id: str
    category_id: str
    name: str
    brand: str
    description: str
    image: str | None = None
    files: list[str] = Field(default_factory=list)
    price: float | None = None
    discount_percentage: float | None = None
    discounted_price: float | None = None
    stock: int
    score: float
    reason: str


class RecommendResponse(BaseModel):
    """Response payload returned by POST /api/recommend."""

    occasion: str
    total_results: int
    recommendations: list[RecommendedProductDTO]
    message: str


class CatalogProductDTO(BaseModel):
    """Public product summary returned by GET /api/products."""

    product_id: str
    vendor_id: str
    category_id: str
    name: str
    brand: str
    description: str
    image: str | None = None
    files: list[str] = Field(default_factory=list)
    price: float | None = None
    discount_percentage: float | None = None
    discounted_price: float | None = None
    stock: int


class CatalogProductsResponse(BaseModel):
    """Paginated response wrapper for eligible catalog items."""

    total_eligible: int
    limit: int
    offset: int
    products: list[CatalogProductDTO]


class HealthResponse(BaseModel):
    """Service health and catalog readiness summary."""

    status: str
    environment: str
    catalog_found: bool
    total_raw_products: int
    eligible_products: int
    excluded_products: int


class OccasionsResponse(BaseModel):
    """List of supported occasion suggestions for quick selection in the UI."""

    occasions: list[str]
