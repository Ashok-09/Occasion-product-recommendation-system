/**
 * Occasion search bar with clear label, submit button, clear button, and quick-pick chips.
 */
export default function SearchBar({
  query,
  onQueryChange,
  onSearch,
  onClear,
  suggestions,
  isLoading,
}) {
  const handleSubmit = (event) => {
    event.preventDefault();
    onSearch(query);
  };

  const handleChipClick = (occasion) => {
    onQueryChange(occasion);
    onSearch(occasion);
  };

  return (
    <section className="search-panel" aria-label="Occasion search">
      <form className="search-form" onSubmit={handleSubmit} noValidate>
        <label className="search-label" htmlFor="occasion-input">
          What occasion are you shopping for?
        </label>

        <div className="search-controls">
          <div className="input-wrapper">
            <input
              id="occasion-input"
              type="text"
              className="occasion-input"
              value={query}
              onChange={(event) => onQueryChange(event.target.value)}
              placeholder="e.g., Birthday, Wedding, Diwali, Valentine's Day, Office Party..."
              maxLength={120}
              disabled={isLoading}
              autoComplete="off"
            />
            {query && !isLoading && (
              <button
                type="button"
                className="clear-btn"
                onClick={onClear}
                aria-label="Clear occasion input"
              >
                ×
              </button>
            )}
          </div>

          <button type="submit" className="recommend-btn" disabled={isLoading}>
            {isLoading ? "Finding Gifts..." : "Find Recommendations"}
          </button>
        </div>
      </form>

      {suggestions.length > 0 && (
        <div className="suggestions-row">
          <span className="suggestions-label">Try an occasion:</span>
          <div className="chips-list" role="list">
            {suggestions.map((occasion) => {
              const isActive = query.trim().toLowerCase() === occasion.toLowerCase();
              return (
                <button
                  key={occasion}
                  type="button"
                  role="listitem"
                  className={`occasion-chip ${isActive ? "active" : ""}`}
                  onClick={() => handleChipClick(occasion)}
                  disabled={isLoading}
                >
                  {occasion}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}
