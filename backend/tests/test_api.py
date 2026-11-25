"""API endpoint integration tests for Phase 5."""

import json
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings, get_settings
from app.main import create_app


def test_health_endpoint_reports_catalog_counts() -> None:
    """GET /api/health returns ok status and exact real catalog counts."""
    with TestClient(create_app()) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["catalog_found"] is True
    assert body["total_raw_products"] == 110
    assert body["eligible_products"] == 104
    assert body["excluded_products"] == 6


def test_occasions_endpoint_returns_curated_list() -> None:
    """GET /api/occasions exposes supported occasions for UI chips."""
    with TestClient(create_app()) as client:
        response = client.get("/api/occasions")

    assert response.status_code == 200
    occasions = response.json()["occasions"]
    assert "Birthday" in occasions
    assert "Diwali" in occasions
    assert "Wedding" in occasions


def test_products_endpoint_supports_pagination() -> None:
    """GET /api/products returns eligible products with limit/offset slicing."""
    with TestClient(create_app()) as client:
        response = client.get("/api/products?limit=5&offset=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total_eligible"] == 104
    assert body["limit"] == 5
    assert body["offset"] == 2
    assert len(body["products"]) == 5


def test_recommend_valid_occasion_returns_ranked_payload() -> None:
    """POST /api/recommend returns sorted recommendations with required catalog fields."""
    with TestClient(create_app()) as client:
        response = client.post("/api/recommend", json={"occasion": "Diwali", "top_k": 5})

    assert response.status_code == 200
    body = response.json()
    assert body["occasion"] == "Diwali"
    assert body["total_results"] == 5
    assert len(body["recommendations"]) == 5
    first = body["recommendations"][0]
    assert "diwali" in first["name"].lower()
    assert first["image"].startswith("https://")
    assert first["score"] > 0
    assert first["reason"]


def test_recommend_unknown_occasion_returns_empty_with_message() -> None:
    """POST /api/recommend returns 0 results and helpful empty-state message for unknown inputs."""
    with TestClient(create_app()) as client:
        response = client.post("/api/recommend", json={"occasion": "xyz123unknown"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_results"] == 0
    assert body["recommendations"] == []
    assert "No strong matches found" in body["message"]


def test_recommend_validation_errors() -> None:
    """Empty/whitespace occasion or missing body field returns HTTP 422."""
    with TestClient(create_app()) as client:
        blank_resp = client.post("/api/recommend", json={"occasion": "   "})
        missing_resp = client.post("/api/recommend", json={})

    assert blank_resp.status_code == 422
    assert missing_resp.status_code == 422


def test_missing_catalog_returns_503_gracefully(tmp_path: Path) -> None:
    """Degraded app state returns 503 on /recommend instead of crashing with 500."""
    base = get_settings()
    broken_settings = Settings(
        app_name=base.app_name,
        app_env="test",
        host=base.host,
        port=base.port,
        catalog_path=tmp_path / "missing.json",
        cors_origins=base.cors_origins,
    )
    with TestClient(create_app(broken_settings)) as client:
        health = client.get("/api/health")
        rec = client.post("/api/recommend", json={"occasion": "Birthday"})

    assert health.status_code == 200
    assert health.json()["status"] == "degraded"
    assert rec.status_code == 503


def test_empty_catalog_returns_zero_recommendations(tmp_path: Path) -> None:
    """An empty JSON list catalog starts cleanly and returns 0 recommendations."""
    empty_file = tmp_path / "empty.json"
    empty_file.write_text(json.dumps([]), encoding="utf-8")

    base = get_settings()
    empty_settings = Settings(
        app_name=base.app_name,
        app_env="test",
        host=base.host,
        port=base.port,
        catalog_path=empty_file,
        cors_origins=base.cors_origins,
    )
    with TestClient(create_app(empty_settings)) as client:
        rec = client.post("/api/recommend", json={"occasion": "Birthday"})

    assert rec.status_code == 200
    assert rec.json()["total_results"] == 0
