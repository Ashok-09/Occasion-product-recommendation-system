import { useEffect, useState } from "react";
import { fetchOccasions, fetchRecommendations } from "./api/client.js";
import ProductGrid from "./components/ProductGrid.jsx";
import SearchBar from "./components/SearchBar.jsx";

const FALLBACK_OCCASIONS = [
  "Birthday",
  "Wedding",
  "Diwali",
  "Valentine's Day",
  "Office Party",
  "Anniversary",
  "Housewarming",
  "Christmas",
];

export default function App() {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState(FALLBACK_OCCASIONS);
  const [activeOccasion, setActiveOccasion] = useState("");
  const [results, setResults] = useState([]);
  const [statusMessage, setStatusMessage] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let mounted = true;
    fetchOccasions()
      .then((occasions) => {
        if (mounted && occasions.length > 0) {
          setSuggestions(occasions);
        }
      })
      .catch(() => {
        // Keep built-in fallback occasion chips if backend is temporarily unreachable.
      });

    return () => {
      mounted = false;
    };
  }, []);

  const handleSearch = async (occasionText) => {
    const trimmed = (occasionText || "").trim();
    if (!trimmed) {
      setErrorMessage("Please enter an occasion before searching (for example, Birthday or Diwali).");
      return;
    }

    setIsLoading(true);
    setErrorMessage("");
    setActiveOccasion(trimmed);

    try {
      const data = await fetchRecommendations(trimmed, 12);
      setResults(Array.isArray(data.recommendations) ? data.recommendations : []);
      setStatusMessage(data.message || "");
      setHasSearched(true);
    } catch (err) {
      setResults([]);
      setErrorMessage(
        err instanceof Error
          ? err.message
          : "Something went wrong while fetching recommendations."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setQuery("");
    setActiveOccasion("");
    setResults([]);
    setStatusMessage("");
    setHasSearched(false);
    setErrorMessage("");
  };

  return (
    <div className="page-wrapper">
      <header className="hero-header">
        <div className="hero-inner">
          <span className="brand-eyebrow">AI/ML Occasion Recommender</span>
          <h1>Occasion-Based Product Recommendation System</h1>
          <p className="hero-subtitle">
            Describe any celebration, festival, or milestone to discover ranked gift ideas matched
            from our curated catalog using hybrid TF-IDF and occasion concept scoring.
          </p>
        </div>
      </header>

      <main className="main-container">
        <SearchBar
          query={query}
          onQueryChange={setQuery}
          onSearch={handleSearch}
          onClear={handleClear}
          suggestions={suggestions}
          isLoading={isLoading}
        />

        <ProductGrid
          hasSearched={hasSearched}
          activeOccasion={activeOccasion}
          results={results}
          statusMessage={statusMessage}
          isLoading={isLoading}
          errorMessage={errorMessage}
        />
      </main>
    </div>
  );
}
