"""Hybrid occasion-based product recommendation engine using TF-IDF and concept matching."""

from dataclasses import dataclass
import logging
import re

from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import RecommendationConfig
from app.schemas import ProductRecord


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OccasionConcept:
    """Curated occasion terms grounded in actual catalog themes for query expansion."""

    canonical_name: str
    aliases: tuple[str, ...]
    primary_terms: tuple[str, ...]
    secondary_terms: tuple[str, ...]


# Each concept group contains terms that appear in our product catalog so query
# expansion bridges user intent (e.g., "Valentine's Day") with real catalog vocabulary.
OCCASION_CONCEPTS: tuple[OccasionConcept, ...] = (
    OccasionConcept(
        canonical_name="Birthday",
        aliases=("birthday", "bday", "birthdays", "birthday party", "kids birthday"),
        primary_terms=(
            "birthday",
            "birthdays",
            "celebration",
            "celebrations",
            "bouquet",
            "flower",
            "flowers",
            "chocolate",
            "chocolates",
            "teddy",
            "plushies",
            "greeting card",
            "greeting cards",
            "gift box",
            "gift boxes",
            "gift wrapping",
            "gift sets",
        ),
        secondary_terms=(
            "gift",
            "gifts",
            "gifting",
            "candle",
            "candles",
            "perfume",
            "watch",
            "toys",
            "joy",
            "surprise",
        ),
    ),
    OccasionConcept(
        canonical_name="Wedding",
        aliases=("wedding", "weddings", "marriage", "bridal", "shaadi"),
        primary_terms=(
            "wedding",
            "weddings",
            "engagement",
            "saree",
            "sarees",
            "suit",
            "suits",
            "choker",
            "necklace",
            "bracelet",
            "earrings",
            "pearl",
            "gold",
            "flower",
            "flowers",
            "bouquet",
            "lilies",
            "marigold",
        ),
        secondary_terms=(
            "celebration",
            "celebrations",
            "traditional",
            "elegant",
            "festive",
            "luxury",
            "gift sets",
            "perfume",
        ),
    ),
    OccasionConcept(
        canonical_name="Anniversary",
        aliases=("anniversary", "anniversaries", "wedding anniversary"),
        primary_terms=(
            "anniversary",
            "anniversaries",
            "romantic",
            "romance",
            "couple",
            "couples",
            "forever rose",
            "rose",
            "star map",
            "story book",
            "perfume",
            "perfumes",
            "necklace",
            "bracelet",
            "watch",
            "touch bracelets",
        ),
        secondary_terms=(
            "love",
            "milestone",
            "chocolates",
            "candle",
            "candles",
            "bouquet",
            "flowers",
            "memories",
        ),
    ),
    OccasionConcept(
        canonical_name="Valentine's Day",
        aliases=("valentine's day", "valentines day", "valentine", "valentines", "romantic", "date night"),
        primary_terms=(
            "valentine",
            "romantic",
            "romance",
            "love",
            "couple",
            "couples",
            "forever rose",
            "rose",
            "cherry blossom",
            "chocolates",
            "luxury chocolates",
            "perfume",
            "perfumes",
            "body oils",
            "touch bracelets",
            "open when letters",
        ),
        secondary_terms=(
            "bouquet",
            "flowers",
            "candle",
            "candles",
            "teddy",
            "mugs",
            "star map",
            "heartfelt",
        ),
    ),
    OccasionConcept(
        canonical_name="Diwali",
        aliases=("diwali", "deepavali", "diwali festival"),
        primary_terms=(
            "diwali",
            "dry fruits",
            "hampers",
            "hamper",
            "festive",
            "festival",
            "traditional",
            "indian",
            "sarees",
            "kurtis",
            "suits",
            "choker",
            "gold",
            "earrings",
            "marigold",
        ),
        secondary_terms=(
            "luxury",
            "prosperity",
            "candles",
            "candle",
            "gift sets",
            "gift boxes",
            "celebration",
        ),
    ),
    OccasionConcept(
        canonical_name="Christmas",
        aliases=("christmas", "xmas", "holiday", "holiday season"),
        primary_terms=(
            "christmas",
            "holiday",
            "hampers",
            "hamper",
            "dry fruits",
            "festive",
            "seasonal",
            "candle",
            "candles",
            "chocolate",
            "chocolates",
            "gift sets",
            "gift boxes",
        ),
        secondary_terms=(
            "warmth",
            "celebration",
            "greeting cards",
            "gift wrapping",
            "snacks",
        ),
    ),
    OccasionConcept(
        canonical_name="Holi",
        aliases=("holi", "festival of colors"),
        primary_terms=(
            "holi",
            "festival of colors",
            "dry fruits",
            "hampers",
            "hamper",
            "festive",
            "vibrant",
            "kurtis",
            "traditional",
        ),
        secondary_terms=(
            "celebration",
            "organic",
            "skincare",
            "bath salts",
            "gift",
        ),
    ),
    OccasionConcept(
        canonical_name="Office Party",
        aliases=("office party", "office", "corporate", "corporate event", "work party", "team celebration"),
        primary_terms=(
            "office",
            "corporate",
            "work",
            "workplace",
            "employees",
            "employee",
            "executive",
            "pen",
            "pens",
            "shirts",
            "office wears",
            "watch",
            "self-care",
            "wellness",
        ),
        secondary_terms=(
            "formal",
            "semi-formal",
            "polo",
            "notebooks",
            "journals",
            "gift cards",
            "hampers",
        ),
    ),
    OccasionConcept(
        canonical_name="Graduation",
        aliases=("graduation", "convocation", "farewell", "new job"),
        primary_terms=(
            "milestone",
            "milestones",
            "executive",
            "pen",
            "pens",
            "fountain pens",
            "watch",
            "notebooks",
            "journals",
            "gift cards",
            "digital gift cards",
            "celebration",
        ),
        secondary_terms=(
            "shirts",
            "bouquet",
            "flowers",
            "greeting cards",
            "chocolates",
        ),
    ),
    OccasionConcept(
        canonical_name="Housewarming",
        aliases=("housewarming", "new home", "griha pravesh"),
        primary_terms=(
            "housewarming",
            "new home",
            "home",
            "decor",
            "décor",
            "indoor plants",
            "planters",
            "candles",
            "candle",
            "natural fiber",
            "bamboo",
            "upcycled",
        ),
        secondary_terms=(
            "warmth",
            "comfort",
            "new beginnings",
            "living spaces",
            "lilies",
            "marigold",
        ),
    ),
    OccasionConcept(
        canonical_name="Mother's Day",
        aliases=("mother's day", "mothers day", "mom", "mother"),
        primary_terms=(
            "skincare",
            "organic",
            "bath salts",
            "scrubs",
            "herbal teas",
            "self-care",
            "wellness",
            "flower",
            "flowers",
            "bouquet",
            "lilies",
            "pearl",
            "sarees",
            "candles",
        ),
        secondary_terms=(
            "necklace",
            "earrings",
            "greeting cards",
            "perfume",
            "soaps",
            "relax",
        ),
    ),
    OccasionConcept(
        canonical_name="Engagement",
        aliases=("engagement", "ring ceremony"),
        primary_terms=(
            "engagement",
            "couple",
            "couples",
            "milestone",
            "love",
            "commitment",
            "forever rose",
            "necklace",
            "bracelet",
            "choker",
            "bouquet",
            "flowers",
        ),
        secondary_terms=(
            "celebrations",
            "luxury",
            "perfumes",
            "watch",
            "sarees",
        ),
    ),
    OccasionConcept(
        canonical_name="Baby Shower",
        aliases=("baby shower", "newborn", "baby"),
        primary_terms=(
            "baby shower",
            "newborn",
            "soft toys",
            "plushies",
            "teddy bears",
            "gentle",
            "keepsakes",
            "new beginnings",
        ),
        secondary_terms=(
            "celebrations",
            "gift boxes",
            "greeting cards",
            "bamboo",
        ),
    ),
)

_STOP_QUERY_WORDS = frozenset(
    {
        "for",
        "a",
        "an",
        "the",
        "of",
        "on",
        "to",
        "in",
        "day",
        "party",
        "gift",
        "gifts",
        "occasion",
        "occasions",
        "event",
        "unknown",
    }
)

# Mutually distinct named festivals: if the query explicitly targets one festival,
# products explicitly titled for a different festival should be down-ranked.
_FESTIVAL_NAMES = ("diwali", "holi", "christmas", "valentine")


class ScoredRecommendation(BaseModel):
    """Single ranked recommendation along with score breakdown and catalog-grounded reason."""

    product: ProductRecord
    score: float
    tfidf_score: float
    title_score: float
    description_score: float
    matched_terms: list[str]
    reason: str


def _normalize_query(text: str) -> str:
    """Lowercase and collapse whitespace/punctuation nuances for clean occasion matching."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip().lower())
    return cleaned


def _tokenize(text: str) -> list[str]:
    """Extract meaningful alphanumeric word tokens while stripping possessives ('s)."""
    without_possessive = re.sub(r"['’]s\b", "", text.lower())
    return [tok for tok in re.findall(r"[a-z0-9]+", without_possessive) if len(tok) > 1]


def _contains_term(haystack: str, term: str) -> bool:
    """Check whole-word or whole-phrase presence inside lowercase text."""
    if not haystack or not term:
        return False
    pattern = r"\b" + re.escape(term.lower()) + r"\b"
    return re.search(pattern, haystack) is not None


def _resolve_occasion_concept(normalized_query: str) -> OccasionConcept | None:
    """Find the best matching OccasionConcept by exact alias or meaningful phrase overlap."""
    if not normalized_query:
        return None

    # First check exact alias matches (handles e.g. "birthday", "valentine's day", "diwali").
    for concept in OCCASION_CONCEPTS:
        if normalized_query in concept.aliases:
            return concept

    # Next check if a known alias appears inside a longer query (e.g., "sister birthday gift").
    best_concept: OccasionConcept | None = None
    best_alias_len = 0
    for concept in OCCASION_CONCEPTS:
        for alias in concept.aliases:
            if _contains_term(normalized_query, alias) and len(alias) > best_alias_len:
                best_concept = concept
                best_alias_len = len(alias)
    return best_concept


class OccasionRecommender:
    """Hybrid TF-IDF + Occasion Concept recommendation engine over eligible catalog items."""

    def __init__(
        self,
        products: list[ProductRecord],
        config: RecommendationConfig | None = None,
    ) -> None:
        self.products = products
        self.config = config or RecommendationConfig()
        self._vectorizer: TfidfVectorizer | None = None
        self._tfidf_matrix = None
        self._fit_index()

    def _fit_index(self) -> None:
        """Fit TF-IDF vocabulary and document vectors once on the eligible product corpus."""
        if not self.products:
            logger.warning("Initialized OccasionRecommender with an empty product catalog.")
            return

        corpus = [product.searchable_text for product in self.products]
        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True,
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(corpus)
        logger.info(
            "TF-IDF index built for %d products (%d features).",
            len(self.products),
            self._tfidf_matrix.shape[1],
        )

    @staticmethod
    def list_supported_occasions() -> list[str]:
        """Return canonical occasion names supported with concept expansion."""
        return [concept.canonical_name for concept in OCCASION_CONCEPTS]

    def _build_expanded_query(
        self, normalized_query: str, concept: OccasionConcept | None
    ) -> str:
        """Create weighted text query combining raw user words with curated occasion concepts."""
        raw_parts = [normalized_query] * 3
        if concept is None:
            return " ".join(raw_parts)

        primary_part = " ".join(concept.primary_terms)
        secondary_part = " ".join(concept.secondary_terms)
        return " ".join(raw_parts + [primary_part, primary_part, secondary_part])

    def _score_title(
        self,
        product: ProductRecord,
        raw_tokens: list[str],
        concept: OccasionConcept | None,
    ) -> tuple[float, list[str]]:
        """Score direct and concept keyword hits inside the product name."""
        title_lower = product.name.lower()
        matched: list[str] = []

        meaningful_raw = [tok for tok in raw_tokens if tok not in _STOP_QUERY_WORDS]
        raw_hits = [tok for tok in meaningful_raw if _contains_term(title_lower, tok)]
        matched.extend(raw_hits)

        if raw_hits and len(raw_hits) == len(meaningful_raw):
            return 1.0, list(dict.fromkeys(matched))

        if concept is None:
            if not meaningful_raw:
                return 0.0, []
            return len(raw_hits) / len(meaningful_raw), list(dict.fromkeys(matched))

        primary_hits = [
            term for term in concept.primary_terms if _contains_term(title_lower, term)
        ]
        secondary_hits = [
            term for term in concept.secondary_terms if _contains_term(title_lower, term)
        ]
        matched.extend(primary_hits)
        matched.extend(secondary_hits)

        # Weight exact raw tokens highest; cap concept-only title hits below exact title matches.
        points = (len(raw_hits) * 1.2) + (len(primary_hits) * 0.55) + (len(secondary_hits) * 0.25)
        cap = 1.0 if raw_hits else 0.72
        score = min(cap, points / 1.4)
        return score, list(dict.fromkeys(matched))

    def _score_description_and_brand(
        self,
        product: ProductRecord,
        raw_tokens: list[str],
        concept: OccasionConcept | None,
    ) -> tuple[float, list[str]]:
        """Score evidence inside product description, brand, and readable slug context."""
        text_lower = f"{product.description} {product.brand} {product.slug}".lower()
        matched: list[str] = []

        meaningful_raw = [tok for tok in raw_tokens if tok not in _STOP_QUERY_WORDS]
        raw_hits = [tok for tok in meaningful_raw if _contains_term(text_lower, tok)]
        matched.extend(raw_hits)

        if concept is None:
            if not meaningful_raw:
                return 0.0, []
            score = min(1.0, len(raw_hits) / max(1, len(meaningful_raw)))
            return score, list(dict.fromkeys(matched))

        primary_hits = [
            term for term in concept.primary_terms if _contains_term(text_lower, term)
        ]
        secondary_hits = [
            term for term in concept.secondary_terms if _contains_term(text_lower, term)
        ]
        matched.extend(primary_hits)
        matched.extend(secondary_hits)

        # Saturating sum: matching 3-4 strong concepts reaches near full description score.
        weighted_hits = (len(raw_hits) * 1.4) + (len(primary_hits) * 0.9) + (len(secondary_hits) * 0.35)
        score = min(1.0, weighted_hits / 3.0)
        return score, list(dict.fromkeys(matched))

    @staticmethod
    def _build_reason(
        product: ProductRecord,
        occasion_label: str,
        title_matches: list[str],
        desc_matches: list[str],
    ) -> str:
        """Build a short, honest explanation citing only terms found in the product's own text."""
        combined_terms = list(dict.fromkeys(title_matches + desc_matches))
        # Deduplicate plural/singular overlaps (e.g. keep 'flower' or 'flowers', not clutter).
        shown_terms = combined_terms[:4]
        if not shown_terms:
            return f"Semantically related to {occasion_label} based on product description ({product.brand})."

        quoted = ", ".join(f"'{term}'" for term in shown_terms)
        if title_matches and desc_matches:
            location = "product name and description"
        elif title_matches:
            location = "product name"
        else:
            location = "product description"

        if product.brand and product.brand != "Unknown":
            return f"Matches {quoted} in {location} (Brand: {product.brand})."
        return f"Matches {quoted} in {location}."

    def recommend(
        self, occasion: str, top_k: int | None = None
    ) -> list[ScoredRecommendation]:
        """Rank eligible catalog products for a user-entered occasion query."""
        normalized_query = _normalize_query(occasion)
        if not normalized_query or not self.products or self._vectorizer is None:
            return []

        limit = top_k if top_k is not None else self.config.default_top_k
        if limit <= 0:
            return []

        concept = _resolve_occasion_concept(normalized_query)
        raw_tokens = _tokenize(normalized_query)
        expanded_query = self._build_expanded_query(normalized_query, concept)

        query_vec = self._vectorizer.transform([expanded_query])
        raw_cosines = cosine_similarity(query_vec, self._tfidf_matrix).flatten()

        occasion_label = concept.canonical_name if concept else occasion.strip()
        target_festivals = {f for f in _FESTIVAL_NAMES if _contains_term(normalized_query, f)}
        scored_items: list[ScoredRecommendation] = []

        for idx, product in enumerate(self.products):
            # Scale cosine similarity smoothly while preserving 0.0 when no terms overlap.
            tfidf_norm = min(1.0, float(raw_cosines[idx]) * 1.8)
            title_score, title_matches = self._score_title(product, raw_tokens, concept)
            desc_score, desc_matches = self._score_description_and_brand(
                product, raw_tokens, concept
            )

            # For unknown queries (no curated concept), require at least one meaningful query token
            # match in the product text so generic filler words alone don't trigger false hits.
            if concept is None and title_score == 0.0 and desc_score == 0.0:
                continue

            # Evidence guard: require at least one real term or TF-IDF overlap.
            if tfidf_norm == 0.0 and title_score == 0.0 and desc_score == 0.0:
                continue

            combined_score = (
                self.config.tfidf_weight * tfidf_norm
                + self.config.title_weight * title_score
                + self.config.description_weight * desc_score
            )

            if target_festivals:
                product_title_lower = product.name.lower()
                other_festivals = {
                    f
                    for f in _FESTIVAL_NAMES
                    if f not in target_festivals and _contains_term(product_title_lower, f)
                }
                if other_festivals:
                    combined_score *= 0.45

            if product.has_placeholder_text:
                combined_score *= self.config.placeholder_penalty

            combined_score = round(min(1.0, combined_score), 4)
            if combined_score < self.config.min_score_threshold:
                continue

            all_matches = list(dict.fromkeys(title_matches + desc_matches))
            reason = self._build_reason(product, occasion_label, title_matches, desc_matches)

            scored_items.append(
                ScoredRecommendation(
                    product=product,
                    score=combined_score,
                    tfidf_score=round(tfidf_norm, 4),
                    title_score=round(title_score, 4),
                    description_score=round(desc_score, 4),
                    matched_terms=all_matches,
                    reason=reason,
                )
            )

        scored_items.sort(
            key=lambda item: (-item.score, -item.title_score, item.product.name.lower())
        )
        return scored_items[:limit]
