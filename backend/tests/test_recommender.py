"""Unit tests for Phase 4 hybrid occasion recommendation engine."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.data_loader import load_and_preprocess_catalog
from app.recommender import OccasionRecommender


def _build_real_recommender() -> OccasionRecommender:
    settings = get_settings()
    loaded = load_and_preprocess_catalog(settings.catalog_path)
    return OccasionRecommender(loaded.products, settings.recommendation)


def test_diwali_ranks_diwali_hampers_highest() -> None:
    """Diwali query must place actual Diwali hampers at the very top."""
    engine = _build_real_recommender()
    results = engine.recommend("Diwali", top_k=5)

    assert len(results) > 0
    top_names = [r.product.name.lower() for r in results[:2]]
    assert all("diwali" in name for name in top_names)
    assert results[0].score >= results[1].score


def test_birthday_returns_relevant_celebration_gifts() -> None:
    """Birthday query should recommend bouquets, greeting cards, plushies, or gift sets."""
    engine = _build_real_recommender()
    results = engine.recommend("Birthday", top_k=8)

    assert len(results) >= 4
    names_combined = " | ".join(r.product.name.lower() for r in results)
    assert any(term in names_combined for term in ("flower", "gretting cards", "teddy", "gift"))
    # Ensure placeholder gibberish 'rose' does not outrank real flower bouquets.
    flower_ranks = [
        idx for idx, r in enumerate(results) if r.product.product_id == "cmlavyh2a0005v8ool6hzt8s4"
    ]
    gibberish_ranks = [
        idx for idx, r in enumerate(results) if r.product.product_id == "cmkz8m2lc002ens01sagxf4aa"
    ]
    if flower_ranks and gibberish_ranks:
        assert flower_ranks[0] < gibberish_ranks[0]


def test_wedding_and_anniversary_and_valentines_relevance() -> None:
    """Wedding, Anniversary, and Valentine's Day should return distinct domain-appropriate gifts."""
    engine = _build_real_recommender()

    wedding = engine.recommend("Wedding", top_k=6)
    assert len(wedding) >= 3
    wedding_text = " ".join(r.product.name.lower() + " " + r.product.description.lower() for r in wedding)
    assert any(word in wedding_text for word in ("wedding", "flower", "choker", "saree", "engagement"))

    anniversary = engine.recommend("Anniversary", top_k=6)
    assert len(anniversary) >= 3
    anniv_text = " ".join(r.product.name.lower() + " " + r.product.description.lower() for r in anniversary)
    assert any(word in anniv_text for word in ("anniversary", "romantic", "couple", "forever rose"))

    valentine = engine.recommend("Valentine's Day", top_k=6)
    assert len(valentine) >= 3
    val_text = " ".join(r.product.name.lower() for r in valentine)
    assert any(word in val_text for word in ("forever rose", "couple", "chocolate", "flower"))


def test_office_party_and_housewarming_relevance() -> None:
    """Office Party should surface corporate/office items and Housewarming should top Housewarming Gifts."""
    engine = _build_real_recommender()

    office = engine.recommend("Office Party", top_k=6)
    assert len(office) >= 3
    office_text = " ".join(r.product.name.lower() + " " + r.product.description.lower() for r in office)
    assert any(word in office_text for word in ("office", "corporate", "pen", "shirts"))

    housewarming = engine.recommend("Housewarming", top_k=5)
    assert len(housewarming) >= 2
    assert housewarming[0].product.name == "Housewarming Gifts"


def test_unknown_and_empty_occasions_return_no_results() -> None:
    """Unknown/irrelevant queries and blank strings must return empty recommendations."""
    engine = _build_real_recommender()

    assert engine.recommend("") == []
    assert engine.recommend("   ") == []
    assert engine.recommend("xyz123unknownfestival") == []
    assert engine.recommend("Unknown Occasion xyz") == []
    assert engine.recommend("car engine carburetor") == []


def test_reasons_only_cite_actual_product_text() -> None:
    """Verify every explanation only references matched terms present in the product text."""
    engine = _build_real_recommender()
    results = engine.recommend("Diwali", top_k=5)

    for item in results:
        haystack = (
            f"{item.product.name} {item.product.description} "
            f"{item.product.brand} {item.product.slug}"
        ).lower()
        for term in item.matched_terms:
            assert term.lower() in haystack
        assert item.reason
