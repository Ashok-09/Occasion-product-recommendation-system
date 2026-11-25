"""Unit tests for Phase 3 catalog ingestion, mapping, and preprocessing."""

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.data_loader import (
    CatalogLoadError,
    clean_whitespace,
    is_placeholder_description,
    load_and_preprocess_catalog,
    map_raw_product,
)


def test_real_catalog_counts_and_filtering() -> None:
    """Verify actual products.json loads 110 total, 104 eligible, and 6 excluded items."""
    catalog_path = get_settings().catalog_path
    loaded = load_and_preprocess_catalog(catalog_path)

    assert loaded.stats.total_records == 110
    assert loaded.stats.eligible_records == 104
    assert loaded.stats.excluded_records == 6
    assert loaded.stats.duplicate_ids_removed == 0
    assert loaded.stats.duplicate_names_in_eligible == {"flower": 2}
    assert loaded.stats.placeholder_records_flagged == 4
    assert len(loaded.products) == 104


def test_real_catalog_preserves_ids_images_and_distinct_variants() -> None:
    """Ensure IDs and URLs stay intact and both distinct 'Flower' products remain."""
    loaded = load_and_preprocess_catalog(get_settings().catalog_path)
    flower_items = [p for p in loaded.products if p.name.lower() == "flower"]

    assert len(flower_items) == 2
    ids = {p.product_id for p in flower_items}
    assert ids == {"cmlavyh2a0005v8ool6hzt8s4", "cmmxgiyuv0001v86gwypmc4am"}
    for product in loaded.products:
        assert product.product_id
        assert product.image is not None and product.image.startswith("https://")
        assert product.files == [product.image]
        assert product.searchable_text


def test_real_catalog_excluded_reasons() -> None:
    """Check that unapproved DRAFT and REVIEW_REQUIRED products are excluded with clear reasons."""
    loaded = load_and_preprocess_catalog(get_settings().catalog_path)
    excluded_by_id = {item.product_id: item for item in loaded.stats.excluded_details}

    assert "cmmertyb80001v8m8kl9qc977" in excluded_by_id
    assert "REVIEW_REQUIRED" in excluded_by_id["cmmertyb80001v8m8kl9qc977"].reason
    assert "cmm1welo2001ns0012jpknfwr" in excluded_by_id
    assert "DRAFT" in excluded_by_id["cmm1welo2001ns0012jpknfwr"].reason


def test_text_normalization_and_placeholder_detection() -> None:
    """Verify whitespace cleanup and detection of test/gibberish descriptions."""
    assert clean_whitespace("  Hello \r\n  World \n ") == "Hello World"
    assert is_placeholder_description("gcdyuvdcbdjhbc", "gcdyuvdcbdjhbc") is True
    assert is_placeholder_description("deepesh created", "deepesh created") is True
    assert is_placeholder_description("Handcrafted bouquet of fresh roses", "") is False


def test_missing_fields_and_invalid_image_handling() -> None:
    """Ensure optional missing fields and malformed image URLs degrade gracefully."""
    mapped = map_raw_product(
        {
            "id": "test-1",
            "name": "  Sample   Gift  ",
            "brand": None,
            "description": "",
            "shortDescription": "Fallback short description",
            "mainImage": "not-a-valid-url",
            "price": "not-a-number",
        }
    )

    assert mapped.product_id == "test-1"
    assert mapped.name == "Sample Gift"
    assert mapped.brand == "Unknown"
    assert mapped.description == "Fallback short description"
    assert mapped.image is None
    assert mapped.files == []
    assert mapped.price is None


def test_duplicate_ids_and_deleted_records_filtered(tmp_path: Path) -> None:
    """Verify duplicate IDs are deduplicated and deletedAt records are excluded."""
    sample_file = tmp_path / "catalog.json"
    sample_data = [
        {
            "id": "p-1",
            "name": "Rose Bouquet",
            "description": "Fresh red roses",
            "isApproved": True,
            "status": "ACTIVE",
            "deletedAt": None,
        },
        {
            "id": "p-1",
            "name": "Rose Bouquet Duplicate",
            "description": "Fresh red roses",
            "isApproved": True,
            "status": "ACTIVE",
            "deletedAt": None,
        },
        {
            "id": "p-2",
            "name": "Deleted Item",
            "description": "Old item",
            "isApproved": True,
            "status": "ACTIVE",
            "deletedAt": "2026-02-01T00:00:00Z",
        },
    ]
    sample_file.write_text(json.dumps(sample_data), encoding="utf-8")

    loaded = load_and_preprocess_catalog(sample_file)
    assert loaded.stats.total_records == 3
    assert loaded.stats.eligible_records == 1
    assert loaded.stats.duplicate_ids_removed == 1
    assert loaded.stats.excluded_records == 1
    assert "deletedAt=" in loaded.stats.excluded_details[0].reason


def test_invalid_catalog_file_raises_error(tmp_path: Path) -> None:
    """Raise CatalogLoadError when file is missing or JSON root is not a list."""
    with pytest.raises(CatalogLoadError):
        load_and_preprocess_catalog(tmp_path / "missing.json")

    bad_root = tmp_path / "bad.json"
    bad_root.write_text('{"not": "a list"}', encoding="utf-8")
    with pytest.raises(CatalogLoadError):
        load_and_preprocess_catalog(bad_root)
