"""Catalog ingestion, schema mapping, eligibility filtering, and text preprocessing."""

from collections import Counter
import json
import logging
from pathlib import Path
import re
from typing import Any

from app.schemas import (
    CatalogLoadStats,
    ExcludedProductInfo,
    LoadedCatalog,
    ProductRecord,
)


logger = logging.getLogger(__name__)

# Fields we track for missing/null/empty reporting across the raw catalog.
TRACKED_RAW_FIELDS = (
    "id",
    "shopId",
    "categoryId",
    "name",
    "description",
    "shortDescription",
    "mainImage",
    "brand",
    "price",
    "discountPercentage",
    "stock",
    "hsnCode",
    "deletedAt",
    "rejectionReason",
    "updatedBy",
)

# Known internal test/placeholder markers observed in catalog inspection.
_INTERNAL_TEST_MARKERS = (
    "created by deepesh",
    "deepesh created",
)


class CatalogLoadError(RuntimeError):
    """Raised when the source catalog file cannot be read or fails structural validation."""


def clean_whitespace(value: Any) -> str:
    """Convert any text-like value into a single-spaced, trimmed string."""
    if value is None:
        return ""
    text = str(value).replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", text).strip()


def _parse_optional_float(value: Any) -> float | None:
    """Parse numeric strings or numbers safely, returning None when invalid."""
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _parse_optional_int(value: Any, default: int = 0) -> int:
    """Parse integer quantities safely with a fallback default."""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _extract_valid_image_url(value: Any) -> str | None:
    """Keep valid http/https image URLs untouched while rejecting malformed strings."""
    cleaned = clean_whitespace(value)
    if cleaned.startswith("https://") or cleaned.startswith("http://"):
        return cleaned
    return None


def _compute_discounted_price(
    price: float | None, discount_percentage: float | None
) -> float | None:
    """Calculate final selling price when both price and a valid discount exist."""
    if price is None:
        return None
    if discount_percentage is None or discount_percentage <= 0:
        return round(price, 2)
    bounded_discount = min(discount_percentage, 100.0)
    return round(price * (1.0 - bounded_discount / 100.0), 2)


def _extract_slug_hints(slug: str) -> str:
    """Extract readable words from a product slug without inventing new terms."""
    if not slug:
        return ""
    # Replace hyphens with spaces and strip trailing random CUID-like alphanumeric tokens.
    tokens = re.split(r"[-_\s]+", slug)
    readable_tokens = [
        tok
        for tok in tokens
        if tok and not (len(tok) >= 6 and any(c.isdigit() for c in tok) and any(c.isalpha() for c in tok))
    ]
    return " ".join(readable_tokens)


def _looks_like_gibberish(text: str) -> bool:
    """Detect single-word keyboard-mash strings (e.g., 'gcdyuvdcbdjhbc') using vowel ratio."""
    words = re.findall(r"[a-zA-Z]+", text.lower())
    if len(words) != 1:
        return False
    word = words[0]
    if len(word) < 8:
        return False
    vowels = sum(1 for ch in word if ch in "aeiou")
    return (vowels / len(word)) < 0.18


def is_placeholder_description(description: str, short_description: str) -> bool:
    """Identify test/placeholder text so recommendation scoring can handle it transparently."""
    combined = f"{description} {short_description}".strip().lower()
    if not combined:
        return True
    if any(marker in combined for marker in _INTERNAL_TEST_MARKERS):
        return True
    if _looks_like_gibberish(description):
        return True
    return False


def _evaluate_eligibility(raw: dict[str, Any]) -> tuple[bool, list[str]]:
    """Apply catalog business rules: approved, ACTIVE status, and not soft-deleted."""
    reasons: list[str] = []
    if raw.get("isApproved") is not True:
        reasons.append(f"isApproved={raw.get('isApproved')}")
    if raw.get("status") != "ACTIVE":
        reasons.append(f"status={raw.get('status')}")
    if raw.get("deletedAt") is not None:
        reasons.append(f"deletedAt={raw.get('deletedAt')}")
    return len(reasons) == 0, reasons


def _build_searchable_text(
    name: str,
    brand: str,
    description: str,
    short_description: str,
    slug: str,
) -> str:
    """Combine normalized catalog text fields into one searchable document for ML matching."""
    slug_hints = _extract_slug_hints(slug)
    # Include short_description only if it adds non-redundant words beyond full description.
    parts = [name, brand, description]
    if short_description and short_description.lower() not in description.lower():
        parts.append(short_description)
    if slug_hints:
        parts.append(slug_hints)
    combined = " ".join(part for part in parts if part)
    return clean_whitespace(combined).lower()


def map_raw_product(raw: dict[str, Any]) -> ProductRecord:
    """Map one raw products.json dictionary into a standardized ProductRecord."""
    product_id = clean_whitespace(raw.get("id") or raw.get("product_id") or raw.get("productId"))
    vendor_id = clean_whitespace(raw.get("shopId") or raw.get("vendor_id") or raw.get("vendorId"))
    category_id = clean_whitespace(raw.get("categoryId") or raw.get("vendor_category"))

    name = clean_whitespace(raw.get("name") or raw.get("title")) or "Unnamed Product"
    brand = clean_whitespace(raw.get("brand")) or "Unknown"
    slug = clean_whitespace(raw.get("slug"))

    full_desc = clean_whitespace(raw.get("description"))
    short_desc = clean_whitespace(raw.get("shortDescription"))
    # Prefer full description because many shortDescription fields are truncated at 150 chars.
    primary_desc = full_desc or short_desc

    image_url = _extract_valid_image_url(raw.get("mainImage"))
    files = [image_url] if image_url else []

    price = _parse_optional_float(raw.get("price"))
    discount = _parse_optional_float(raw.get("discountPercentage"))
    discounted_price = _compute_discounted_price(price, discount)
    stock = _parse_optional_int(raw.get("stock"), default=0)
    product_group_id = clean_whitespace(raw.get("productGroupId"))

    placeholder = is_placeholder_description(full_desc, short_desc)
    searchable_text = _build_searchable_text(name, brand, primary_desc, short_desc, slug)

    return ProductRecord(
        product_id=product_id,
        vendor_id=vendor_id,
        category_id=category_id,
        name=name,
        brand=brand,
        slug=slug,
        description=primary_desc,
        short_description=short_desc,
        image=image_url,
        files=files,
        price=price,
        discount_percentage=discount,
        discounted_price=discounted_price,
        stock=stock,
        product_group_id=product_group_id,
        searchable_text=searchable_text,
        has_placeholder_text=placeholder,
    )


def _compute_missing_field_counts(raw_records: list[dict[str, Any]]) -> dict[str, int]:
    """Count missing, null, or empty values for key catalog fields."""
    counts: dict[str, int] = {}
    for field in TRACKED_RAW_FIELDS:
        missing = sum(
            1
            for item in raw_records
            if field not in item or item.get(field) is None or item.get(field) == ""
        )
        counts[field] = missing
    return counts


def load_and_preprocess_catalog(catalog_path: Path) -> LoadedCatalog:
    """Read raw JSON catalog safely, validate records, filter eligible items, and compute stats."""
    if not catalog_path.is_file():
        raise CatalogLoadError(f"Catalog file not found at: {catalog_path}")

    try:
        raw_content = catalog_path.read_text(encoding="utf-8")
        parsed = json.loads(raw_content)
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogLoadError(f"Failed to parse catalog JSON: {exc}") from exc

    if not isinstance(parsed, list):
        raise CatalogLoadError("Catalog JSON root must be a list of product objects.")

    dict_records = [item for item in parsed if isinstance(item, dict)]
    if len(dict_records) != len(parsed):
        logger.warning(
            "Skipped %d non-object entries while loading catalog.",
            len(parsed) - len(dict_records),
        )

    missing_counts = _compute_missing_field_counts(dict_records)

    eligible_products: list[ProductRecord] = []
    excluded_details: list[ExcludedProductInfo] = []
    seen_ids: set[str] = set()
    duplicate_ids_removed = 0

    for raw in dict_records:
        raw_id = clean_whitespace(raw.get("id") or raw.get("product_id") or raw.get("productId"))
        raw_name = clean_whitespace(raw.get("name") or raw.get("title")) or "Unnamed Product"

        if not raw_id:
            excluded_details.append(
                ExcludedProductInfo(
                    product_id="",
                    name=raw_name,
                    status=raw.get("status"),
                    is_approved=raw.get("isApproved"),
                    reason="missing product id",
                )
            )
            continue

        if raw_id in seen_ids:
            duplicate_ids_removed += 1
            logger.info("Skipping duplicate product id=%s (%s)", raw_id, raw_name)
            continue
        seen_ids.add(raw_id)

        is_eligible, reasons = _evaluate_eligibility(raw)
        if not is_eligible:
            excluded_details.append(
                ExcludedProductInfo(
                    product_id=raw_id,
                    name=raw_name,
                    status=raw.get("status"),
                    is_approved=raw.get("isApproved"),
                    reason=", ".join(reasons),
                )
            )
            continue

        eligible_products.append(map_raw_product(raw))

    name_counts = Counter(product.name.lower() for product in eligible_products)
    duplicate_names = {name: count for name, count in name_counts.items() if count > 1}
    placeholder_count = sum(1 for product in eligible_products if product.has_placeholder_text)

    stats = CatalogLoadStats(
        total_records=len(parsed),
        eligible_records=len(eligible_products),
        excluded_records=len(excluded_details),
        duplicate_ids_removed=duplicate_ids_removed,
        duplicate_names_in_eligible=duplicate_names,
        placeholder_records_flagged=placeholder_count,
        missing_field_counts=missing_counts,
        excluded_details=excluded_details,
    )

    logger.info(
        "Loaded catalog: total=%d eligible=%d excluded=%d duplicates_removed=%d placeholders=%d",
        stats.total_records,
        stats.eligible_records,
        stats.excluded_records,
        stats.duplicate_ids_removed,
        stats.placeholder_records_flagged,
    )

    return LoadedCatalog(products=eligible_products, stats=stats)
