import ProductCard from "./ProductCard.jsx";

/**
 * Renders loading skeletons, error alerts, empty states, or ranked product cards
 * directly below the occasion input on the same page.
 */
export default function ProductGrid({
  hasSearched,
  activeOccasion,
  results,
  statusMessage,
  isLoading,
  errorMessage,
}) {
  if (errorMessage) {
    return (
      <section className="status-box error-box" role="alert">
        <h2>Unable to load recommendations</h2>
        <p>{errorMessage}</p>
      </section>
    );
  }

  if (isLoading) {
    return (
      <section className="results-section" aria-busy="true" aria-label="Loading recommendations">
        <div className="results-header">
          <p className="results-summary">Analyzing catalog for "{activeOccasion}"...</p>
        </div>
        <div className="product-grid">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="skeleton-card">
              <div className="skeleton-media" />
              <div className="skeleton-line short" />
              <div className="skeleton-line" />
              <div className="skeleton-line" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (!hasSearched) {
    return (
      <section className="status-box initial-box">
        <h2>Ready to help you find the right gift</h2>
        <p>
          Enter an occasion above or click one of the suggested occasions to view ranked product
          recommendations with relevance scores and match explanations.
        </p>
      </section>
    );
  }

  if (results.length === 0) {
    return (
      <section className="status-box empty-box" role="status">
        <h2>No matching products found for "{activeOccasion}"</h2>
        <p>
          {statusMessage ||
            "We could not find strong matches in our catalog for that query. Try occasions like Birthday, Wedding, Diwali, Valentine's Day, or Office Party."}
        </p>
      </section>
    );
  }

  return (
    <section className="results-section" aria-label="Recommended products">
      <div className="results-header">
        <div>
          <h2>Recommended for "{activeOccasion}"</h2>
          <p className="results-summary">{statusMessage}</p>
        </div>
        <span className="count-badge">
          {results.length} {results.length === 1 ? "result" : "results"}
        </span>
      </div>

      <div className="product-grid">
        {results.map((product, index) => (
          <ProductCard key={product.product_id} product={product} rank={index + 1} />
        ))}
      </div>
    </section>
  );
}
