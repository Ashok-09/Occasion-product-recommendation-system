import { useState } from "react";
import CategoryFallbackVisual from "./CategoryFallbackVisual.jsx";

function formatPrice(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return null;
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

function truncateText(text, maxLength = 145) {
  if (!text) return "No description available for this item.";
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength).trimEnd()}...`;
}

/**
 * Displays one ranked product recommendation with image fallback, pricing, score, and reason.
 */
export default function ProductCard({ product, rank }) {
  const [imageFailed, setImageFailed] = useState(false);

  const hasImage = Boolean(product.image) && !imageFailed;
  const formattedPrice = formatPrice(product.price);
  const formattedDiscounted = formatPrice(product.discounted_price);
  const hasDiscount =
    product.discount_percentage > 0 &&
    formattedDiscounted &&
    formattedPrice &&
    product.discounted_price < product.price;

  const matchPercent = Math.round((product.score || 0) * 100);

  return (
    <article className="product-card">
      <div className="card-media">
        <span className="rank-badge">#{rank}</span>
        <span className="score-badge" title={`Relevance score: ${product.score.toFixed(2)}`}>
          {matchPercent}% match
        </span>

        {hasImage ? (
          <img
            src={product.image}
            alt={product.name}
            className="product-image"
            loading="lazy"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <CategoryFallbackVisual product={product} />
        )}
      </div>

      <div className="card-body">
        <div className="card-meta">
          <span className="brand-tag">{product.brand || "Unknown Brand"}</span>
          {product.category_id && (
            <span className="category-tag" title={`Catalog Category ID: ${product.category_id}`}>
              Cat: {product.category_id.slice(0, 10)}…
            </span>
          )}
        </div>

        <h3 className="product-title">{product.name}</h3>

        <p className="product-description">{truncateText(product.description)}</p>

        <div className="price-row">
          {formattedPrice ? (
            hasDiscount ? (
              <div className="price-group">
                <span className="price-current">{formattedDiscounted}</span>
                <span className="price-original">{formattedPrice}</span>
                <span className="discount-pill">{Math.round(product.discount_percentage)}% off</span>
              </div>
            ) : (
              <span className="price-current">{formattedPrice}</span>
            )
          ) : (
            <span className="price-unavailable">Price not listed</span>
          )}
        </div>

        <div className="reason-box">
          <span className="reason-label">Why it matches:</span>
          <p className="reason-text">{product.reason}</p>
        </div>
      </div>
    </article>
  );
}
