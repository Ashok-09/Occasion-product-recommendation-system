"""Comprehensive QA test suite covering edge cases, data integrity, ranking, and latency."""

import json
from pathlib import Path
import sys
import time

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings, get_settings
from app.data_loader import load_and_preprocess_catalog
from app.main import create_app
from app.recommender import OccasionRecommender


REQUIRED_OCCASIONS = (
    "Birthday",
    "Wedding",
    "Diwali",
    "Anniversary",
    "Valentine's Day",
    "Office Party",
)

EXCLUDED_UNAPPROVED_IDS = {
    "cmmertyb80001v8m8kl9qc977",
    "cmm1welo2001ns0012jpknfwr",
    "cmmkj7nx9001gqk016c1f6zza",
    "cmm39yjan0001v83cei2iir99",
    "cmmkk9q1k0007s201pyd2xwfb",
    "cmkza61ob0051ns01g5cmzox3",
}


def test_required_occasions_consistency_and_no_duplicates() -> None:
    """Every required occasion returns sorted, unique, approved products with valid DTOs."""
    with TestClient(create_app()) as client:
        for occasion in REQUIRED_OCCASIONS:
            resp = client.post("/api/recommend", json={"occasion": occasion, "top_k": 12})
            assert resp.status_code == 200, f"Failed for {occasion}"
            payload = resp.json()
            recs = payload["recommendations"]
            assert payload["total_results"] == len(recs)
            assert len(recs) >= 3, f"Too few results for {occasion}"

            ids = [item["product_id"] for item in recs]
            assert len(ids) == len(set(ids)), f"Duplicate product_ids for {occasion}"
            assert not (set(ids) & EXCLUDED_UNAPPROVED_IDS), "Leaked unapproved product"

            scores = [item["score"] for item in recs]
            assert scores == sorted(scores, reverse=True), "Results not sorted descending"
            for item in recs:
                assert 0.15 <= item["score"] <= 1.0
                assert item["name"]
                assert item["reason"]


def test_invalid_inputs_rejected_with_422() -> None:
    """Empty strings, oversized queries, and out-of-range top_k must return 422."""
    with TestClient(create_app()) as client:
        assert client.post("/api/recommend", json={"occasion": ""}).status_code == 422
        assert client.post("/api/recommend", json={"occasion": "   "}).status_code == 422
        assert client.post("/api/recommend", json={"occasion": "a" * 121}).status_code == 422
        assert client.post("/api/recommend", json={"occasion": "Birthday", "top_k": 0}).status_code == 422
        assert client.post("/api/recommend", json={"occasion": "Birthday", "top_k": 99}).status_code == 422


def test_missing_fields_and_invalid_image_url_via_api(tmp_path: Path) -> None:
    """API cleanly serves eligible products even when optional fields or image URLs are invalid."""
    synthetic_catalog = tmp_path / "synthetic.json"
    synthetic_catalog.write_text(
        json.dumps(
            [
                {
                    "id": "qa-1",
                    "name": "Birthday Gift Hamper",
                    "description": "Festive birthday gift hamper with treats",
                    "mainImage": "invalid-image-url",
                    "brand": None,
                    "price": None,
                    "isApproved": True,
                    "status": "ACTIVE",
                    "deletedAt": None,
                }
            ]
        ),
        encoding="utf-8",
    )

    base = get_settings()
    qa_settings = Settings(
        app_name=base.app_name,
        app_env="test",
        host=base.host,
        port=base.port,
        catalog_path=synthetic_catalog,
        cors_origins=base.cors_origins,
    )
    with TestClient(create_app(qa_settings)) as client:
        resp = client.post("/api/recommend", json={"occasion": "Birthday"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_results"] == 1
    item = body["recommendations"][0]
    assert item["product_id"] == "qa-1"
    assert item["image"] is None
    assert item["files"] == []
    assert item["brand"] == "Unknown"
    assert item["price"] is None


def test_recommendation_engine_latency() -> None:
    """Verify per-query recommendation latency stays well under 50 ms on the real catalog."""
    settings = get_settings()
    loaded = load_and_preprocess_catalog(settings.catalog_path)
    engine = OccasionRecommender(loaded.products, settings.recommendation)

    start = time.perf_counter()
    for occasion in REQUIRED_OCCASIONS:
        engine.recommend(occasion, top_k=12)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    avg_ms = elapsed_ms / len(REQUIRED_OCCASIONS)

    assert avg_ms < 50.0, f"Unexpectedly slow average latency: {avg_ms:.2f} ms"
