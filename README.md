# Occasion-Based Product Recommendation System

An end-to-end AI/ML full-stack web application that accepts a user-entered occasion (such as **Birthday**, **Wedding**, **Diwali**, **Valentine's Day**, **Office Party**, or **Housewarming**), analyzes the provided `products.json` product catalog, and renders ranked product recommendations with relevance scores and catalog-grounded explanations on the same page.

---

## 1. Project Overview

Finding the right gift or product for a specific occasion is hard when users search by *event intent* ("Valentine's Day" or "Housewarming") rather than exact product titles ("Forever Rose" or "Indoor plants & planters"). This project bridges that gap using a deterministic, explainable **Hybrid TF-IDF + Occasion Concept Recommendation Engine** served by **FastAPI** and presented in a responsive **React + Vite** single-page interface.

---

## 2. Problem Statement

Given a real-world e-commerce catalog (`data/products.json`), build a production-structured recommendation application that:
- Safely ingests and cleans catalog data without modifying the source JSON file.
- Filters out unapproved, draft, or deleted products.
- Computes meaningful relevance scores for any occasion entered by the user.
- Displays ranked product cards directly below the search input on a single page, including product image (where available), name, brand, category identifier, description snippet, price, relevance score, and an honest explanation of the match.

---

## 3. Objectives

- Build a modular **data preprocessing pipeline** with schema mapping and audit metrics.
- Design a transparent, low-latency **hybrid recommendation engine** (no paid APIs or external LLM calls required).
- Expose clean, validated **REST endpoints** via FastAPI + Pydantic.
- Deliver a responsive, beginner-friendly **React UI** with loading, empty, error, and image-fallback states.
- Verify behavior with automated **backend (`pytest`)**, **frontend (`Vitest`)**, and live browser integration tests.

---

## 4. System Architecture

```text
+-----------------------------------------------------------------------+
|                    FRONTEND (React 19 + Vite)                         |
|  - SearchBar: labeled occasion input, clear button, quick-pick chips  |
|  - ProductGrid: loading skeletons, error alert, empty state, cards    |
|  - ProductCard: image + fallback, brand, category ID, price, score,   |
|                 "Why it matches" evidence explanation                 |
+-----------------------------------+-----------------------------------+
                                    | HTTP JSON (/api/* via Vite proxy)
                                    v
+-----------------------------------------------------------------------+
|                    BACKEND (Python 3.14 + FastAPI)                    |
|  1. API Layer (backend/app/routes.py + schemas.py)                    |
|     - GET /api/health, /api/occasions, /api/products                  |
|     - POST /api/recommend (Pydantic validation & HTTP status codes)   |
|  2. Data Ingestion Layer (backend/app/data_loader.py)                 |
|     - Loads data/products.json (110 raw -> 104 eligible)              |
|     - Maps JSON fields, normalizes text, flags placeholders           |
|  3. Hybrid Recommendation Engine (backend/app/recommender.py)         |
|     - scikit-learn TfidfVectorizer (1-2 ngrams) + cosine_similarity   |
|     - Occasion concept expansion + field weights + threshold guard    |
+-----------------------------------------------------------------------+
```

### Folder Structure

```text
EMILO TASK/
├── data/
│   └── products.json                  # Original untouched catalog (110 records)
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                  # Environment settings & scoring weights
│   │   ├── data_loader.py             # Ingestion, schema mapping & filtering
│   │   ├── main.py                    # FastAPI app factory & lifespan setup
│   │   ├── recommender.py             # Hybrid TF-IDF + concept matching engine
│   │   ├── routes.py                  # REST API routes
│   │   └── schemas.py                 # Pydantic data & API DTO models
│   ├── tests/
│   │   ├── test_api.py                # Endpoint & error-status tests
│   │   ├── test_data_loader.py        # Catalog audit & preprocessing tests
│   │   ├── test_qa_suite.py           # Consistency, bounds & latency QA tests
│   │   └── test_recommender.py        # Ranking & empty-query ML tests
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.js              # Fetch wrappers for /api endpoints
│   │   ├── components/
│   │   │   ├── ProductCard.jsx        # Product details, price, score & reason
│   │   │   ├── ProductGrid.jsx        # Results grid, loading, empty & error UI
│   │   │   └── SearchBar.jsx          # Occasion input & suggested chips
│   │   ├── test/setup.js              # Vitest + Testing Library setup
│   │   ├── App.jsx                    # Single-page state orchestration
│   │   ├── App.test.jsx               # Frontend UI unit tests
│   │   ├── index.css                  # Responsive layout & card styling
│   │   └── main.jsx                   # React DOM entry point
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

---

## 5. Technology Stack

- **Backend:** Python 3.14, FastAPI, Uvicorn, Pydantic v2, python-dotenv
- **Machine Learning & Scoring:** scikit-learn (`TfidfVectorizer`, `cosine_similarity`)
- **Frontend:** React 19, Vite 6, plain responsive CSS (CSS Grid & Flexbox)
- **Testing:** `pytest`, FastAPI `TestClient` (`httpx`), `Vitest`, React Testing Library (`jsdom`)
- **Data Storage:** Local JSON catalog (`data/products.json`, unmodified)

---

## 6. Dataset Description & Schema Mapping

`data/products.json` contains **110 product records** with **32 fields** each.

### Eligibility Filtering Summary
Only approved, active, non-deleted products are recommended:
- **Rule:** `isApproved == True` AND `status == "ACTIVE"` AND `deletedAt is None`
- **Total raw records:** `110`
- **Eligible products:** `104`
- **Excluded products:** `6` (`4` in `REVIEW_REQUIRED`, `2` in `DRAFT`)

### Schema Mapping Layer (`backend/app/data_loader.py`)
The assignment specification describes generic fields (`product_id`, `vendor_id`, `vendor_category`, `vendor_category_desc`, `title`, `description`, `files`), whereas the supplied `products.json` uses richer e-commerce fields:

| Specification Field | Actual `products.json` Field | Handling in Mapping Layer |
| :--- | :--- | :--- |
| `product_id` | `id` | Preserved directly (`product_id`). |
| `vendor_id` | `shopId` | Mapped to `vendor_id`; `brand` is also extracted for display and search. |
| `vendor_category` | `categoryId` | Preserved as `category_id` (20 unique CUIDs). |
| `vendor_category_desc` | *(Not present in JSON)* | **Not fabricated.** UI displays `Brand` alongside the raw `categoryId` reference. |
| `title` | `name` | Normalized whitespace (`name`). |
| `description` | `description` / `shortDescription` | Full `description` is preferred because `54` `shortDescription` values are truncated at `150` characters. |
| `files` | `mainImage` | Preserved URL mapped to `image` and wrapped as `files: [image]`. |
| Pricing & inventory | `price`, `discountPercentage`, `stock` | Parsed safely to numbers (`discounted_price` computed when discount > 0). |

---

## 7. Data Preprocessing Pipeline

Implemented in `backend/app/data_loader.py`:
1. **Structural validation:** Verifies JSON root is a list of objects; raises `CatalogLoadError` on missing or corrupt files.
2. **Duplicate handling:** Deduplicates identical `id`s if present (`0` in supplied dataset), while preserving distinct product variants that share the same generic name (e.g., two distinct `"Flower"` products under brand `KA`).
3. **Text normalization:** Collapses `\r\n` newlines and extra spaces (`clean_whitespace`) and builds a lowercase `searchable_text` field from `name`, `brand`, `description`, non-redundant `shortDescription`, and readable `slug` tokens.
4. **Placeholder detection:** Flags `4` active records containing test/gibberish descriptions (e.g., `"gcdyuvdcbdjhbc"`, `"deepesh created"`) with `has_placeholder_text = True` instead of silently deleting catalog records.

---

## 8. Recommendation Methodology

Implemented in `backend/app/recommender.py` (`OccasionRecommender`):
1. **TF-IDF Indexing:** On startup, fits `TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)` across all `104` eligible `searchable_text` documents (`2,771` vocabulary features).
2. **Occasion Concept Expansion:** Maps `13` canonical occasions (`Birthday`, `Wedding`, `Anniversary`, `Valentine's Day`, `Diwali`, `Christmas`, `Holi`, `Office Party`, `Graduation`, `Housewarming`, `Mother's Day`, `Engagement`, `Baby Shower`) and their aliases to grounded catalog terms while also supporting arbitrary free-text queries.
3. **Possessive & Wrapper Stop-Word Cleanup:** Strips possessives (`'s`) and ignores generic wrapper words (`"occasion"`, `"event"`, `"unknown"`) so unrelated queries do not trigger false hits.
4. **Festival Exclusivity Guard:** When a user targets a specific festival (such as `"Diwali"`), products explicitly titled for a different festival (`"Holi Dry fruits hampers"`, `"Christmas Dry fruits hampers"`) are down-ranked (`× 0.45`).
5. **Placeholder & Threshold Guards:** Records flagged with `has_placeholder_text` receive a `× 0.35` penalty, and any product below `min_score_threshold = 0.15` is excluded so unknown queries return `0` items cleanly.
6. **Evidence-Based Explanations:** Every returned item includes a `reason` string citing only the exact matched keywords found in that product's `name`, `description`, or `brand`.

---

## 9. Scoring Formula

Each candidate product receives a normalized score in `[0.0, 1.0]`:

$$\text{Score} = 0.45 \times S_{\text{TF-IDF}} + 0.25 \times S_{\text{Title}} + 0.30 \times S_{\text{Description/Brand}}$$

Where:
- $S_{\text{TF-IDF}} = \min(1.0,\; 1.8 \times \text{cosine\_similarity}(\vec{q}_{\text{expanded}}, \vec{d}))$
- $S_{\text{Title}}$ scores exact query word hits in `product.name` up to `1.0` and concept-only title hits up to `0.72`.
- $S_{\text{Description/Brand}}$ measures weighted keyword and concept coverage across `description`, `brand`, and `slug`.
- Multipliers applied when applicable: `× 0.45` for conflicting festival names in title; `× 0.35` for flagged placeholder descriptions.
- Minimum threshold to return: `0.15`.

---

## 10. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service status plus `total_raw_products`, `eligible_products`, and `excluded_products` counts. |
| `GET` | `/api/occasions` | Returns the list of curated occasion suggestions for UI quick-pick chips. |
| `GET` | `/api/products?limit=20&offset=0` | Paginated list of eligible preprocessed catalog products. |
| `POST` | `/api/recommend` | Accepts `{"occasion": "<text>", "top_k": 12}` and returns ranked recommendations with scores and reasons. |

Interactive OpenAPI/Swagger documentation is available at `http://127.0.0.1:8000/docs` when the backend is running.

---

## 11. Installation & Environment Setup

### Prerequisites
- Python `3.11+` (tested on Python `3.14.3`)
- Node.js `18+` and npm (tested on Node `v24.14.0`, npm `11.9.0`)

### 1. Backend Setup
```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### 2. Environment Variables (Optional)
Copy `backend/.env.example` to `backend/.env` if you want to customize host, port, CORS origins, or `CATALOG_PATH`:
```powershell
Copy-Item backend\.env.example backend\.env
```

### 3. Frontend Setup
```powershell
npm --prefix frontend install
```

---

## 12. Running the Application

Open two terminals in the project root (`EMILO TASK/`):

**Terminal 1 — Start Backend (`http://127.0.0.1:8000`):**
```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Start Frontend (`http://localhost:5173`):**
```powershell
npm --prefix frontend run dev
```

Open `http://localhost:5173` in your browser. Vite proxies `/api/*` requests directly to FastAPI on port `8000`.

---

## 13. Testing Instructions

**Run all 25 backend tests (`pytest`):**
```powershell
backend\.venv\Scripts\pytest.exe backend/tests -v
```

**Run all 3 frontend UI tests (`Vitest`):**
```powershell
npm --prefix frontend test
```

**Build frontend production bundle:**
```powershell
npm --prefix frontend run build
```

---

## 14. Sample Inputs and Outputs

### Request (`POST /api/recommend`)
```json
{
  "occasion": "Diwali",
  "top_k": 3
}
```

### Response (`200 OK`, abbreviated)
```json
{
  "occasion": "Diwali",
  "total_results": 3,
  "message": "Found 3 recommended products for 'Diwali'.",
  "recommendations": [
    {
      "product_id": "cml25lds400fgma0155hp1at1",
      "name": "Diwali Dry fruits hampers",
      "brand": "Joy of Giving",
      "price": 1999.0,
      "discounted_price": 1899.05,
      "score": 0.864,
      "reason": "Matches 'diwali', 'dry fruits', 'hampers', 'hamper' in product name and description (Brand: Joy of Giving)."
    },
    {
      "product_id": "cml265ss000gcma01l3qqapo5",
      "name": "Diwali Luxury Gift Hampers",
      "brand": "Joy of Giving",
      "price": 3499.0,
      "discounted_price": 3149.1,
      "score": 0.718,
      "reason": "Matches 'diwali', 'hampers', 'hamper', 'festive' in product name and description (Brand: Joy of Giving)."
    }
  ]
}
```

### Unknown Occasion Request (`"xyz123unknown"`)
Returns `200 OK` with `"total_results": 0`, `"recommendations": []`, and `"message": "No strong matches found for 'xyz123unknown'. Try occasions like Birthday, Wedding, Diwali, Valentine's Day, or Office Party."`.

---

## 15. Limitations & Observations

1. **No category lookup table in `products.json`:** `categoryId` values are raw CUIDs (`cml0ug1d6003to201xuwjkmcn`). Rather than inventing category names, the UI displays `Brand` and the `categoryId` reference.
2. **External image URL availability:** Product image URLs hosted on `https://s3aws.emilo.in/products/...` currently return `HTTP 404 Not Found` from the remote asset server. `ProductCard.jsx` detects load errors via `onError` and displays a clean `"Image Unavailable"` fallback box.
3. **Curated concept dictionary scope:** While free-text queries work via TF-IDF, very niche or slang occasions outside the 13 curated concept groups rely on lexical overlap with catalog text.
4. **Placeholder catalog entries:** `4` active/approved catalog items contain internal test text (e.g., `"gcdyuvdcbdjhbc"`). They are retained in the catalog and down-ranked rather than silently deleted.

---

## 16. Future Improvements

- **Category metadata integration:** Connect a `/categories` lookup table so human-readable category names enrich both UI cards and TF-IDF weighting.
- **Dense semantic embeddings:** Add lightweight Sentence-Transformer embeddings (e.g., `all-MiniLM-L6-v2`) alongside TF-IDF for broader zero-shot occasion generalization as the catalog grows beyond a few hundred items.
- **Price & budget filters:** Allow users to filter occasion recommendations by budget range or in-stock availability.

---

## 17. Libraries & References

- **FastAPI** — https://fastapi.tiangolo.com/
- **Pydantic** — https://docs.pydantic.dev/
- **Uvicorn** — https://www.uvicorn.org/
- **scikit-learn (`TfidfVectorizer`, `cosine_similarity`)** — https://scikit-learn.org/
- **React** — https://react.dev/
- **Vite** — https://vite.dev/
- **pytest** — https://docs.pytest.org/
- **Vitest & React Testing Library** — https://vitest.dev/ | https://testing-library.com/

---

## 18. AI Coding Assistant Usage Disclosure

In accordance with assignment guidelines:
- An AI coding assistant (Google Antigravity) was used under strict step-by-step human review and approval across architecture planning, code scaffolding, unit/QA test authoring, and documentation drafting.
- All dataset counts, schema mappings, scoring weights, and test results documented in this README were directly verified against `data/products.json` and executed test suites.
- The original assignment specification PDF is **not** included in this repository per assignment rules.
