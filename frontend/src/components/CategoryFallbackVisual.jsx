/**
 * Renders a clean, category-matched SVG fallback illustration when a product's
 * remote `mainImage` URL is missing or returns an HTTP error (e.g., 404).
 */

const VISUAL_THEMES = [
  {
    key: "flowers",
    keywords: ["flower", "rose", "lilies", "marigold", "tulip", "bouquet", "blossom"],
    label: "Floral Gift",
    bg: "linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%)",
    accent: "#e11d48",
  },
  {
    key: "jewellery",
    keywords: ["necklace", "necklave", "nacklace", "choker", "bracelet", "earring", "earing", "jewellery"],
    label: "Jewellery",
    bg: "linear-gradient(135deg, #fefce8 0%, #fef08a 100%)",
    accent: "#b45309",
  },
  {
    key: "watch",
    keywords: ["watch"],
    label: "Timepiece",
    bg: "linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)",
    accent: "#4338ca",
  },
  {
    key: "chocolate",
    keywords: ["chocolate", "chocolates", "snacks"],
    label: "Gourmet Treats",
    bg: "linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%)",
    accent: "#9a3412",
  },
  {
    key: "fragrance",
    keywords: ["perfume", "soap", "candle", "skincare", "bath salt", "scrub", "body oil", "self-care", "wellness", "tea"],
    label: "Fragrance & Care",
    bg: "linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%)",
    accent: "#7e22ce",
  },
  {
    key: "apparel",
    keywords: ["shirt", "office wear", "cargo", "jeans", "pant", "tshirt", "kurti", "saree", "suit", "print"],
    label: "Apparel",
    bg: "linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)",
    accent: "#0369a1",
  },
  {
    key: "toys",
    keywords: ["plush", "teddy", "slime", "craft", "paint", "drum", "xylophone", "dj", "guitar", "toy"],
    label: "Toys & Crafts",
    bg: "linear-gradient(135deg, #ecfeff 0%, #cffafe 100%)",
    accent: "#0e7490",
  },
  {
    key: "decor",
    keywords: ["bamboo", "plant", "planter", "décor", "decor", "upcycled", "bag"],
    label: "Home & Eco Living",
    bg: "linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)",
    accent: "#15803d",
  },
  {
    key: "stationery",
    keywords: ["pen", "notebook", "journal", "star map", "story book", "letter", "card"],
    label: "Keepsakes & Cards",
    bg: "linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)",
    accent: "#334155",
  },
  {
    key: "hamper",
    keywords: ["hamper", "dry fruits", "gift", "housewarming", "engagement", "baby shower", "wax seal"],
    label: "Curated Gift Hamper",
    bg: "linear-gradient(135deg, #fffbeb 0%, #fde68a 100%)",
    accent: "#b45309",
  },
];

const DEFAULT_THEME = {
  key: "hamper",
  label: "Curated Gift",
  bg: "linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)",
  accent: "#1d4ed8",
};

function hasWholeWord(text, term) {
  const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`\\b${escaped}`, "i").test(text);
}

function resolveVisualTheme(product) {
  const title = product.name || "";
  const description = product.description || "";

  // Match product name first using whole-word boundaries so words like "crafted" don't match "craft".
  for (const theme of VISUAL_THEMES) {
    if (theme.keywords.some((word) => hasWholeWord(title, word))) {
      return theme;
    }
  }
  for (const theme of VISUAL_THEMES) {
    if (theme.keywords.some((word) => hasWholeWord(description, word))) {
      return theme;
    }
  }
  return DEFAULT_THEME;
}

function CategoryIcon({ themeKey, color }) {
  const common = {
    width: 44,
    height: 44,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: color,
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": "true",
  };

  switch (themeKey) {
    case "flowers":
      return (
        <svg {...common}>
          <circle cx="12" cy="9" r="2.5" />
          <path d="M12 6.5a2.5 2.5 0 1 1 2.2-3.7A2.5 2.5 0 1 1 16.5 7a2.5 2.5 0 1 1-1.5 4.2A2.5 2.5 0 1 1 12 13.5a2.5 2.5 0 1 1-3-2.3A2.5 2.5 0 1 1 7.5 7a2.5 2.5 0 1 1 2.3-4.2A2.5 2.5 0 0 1 12 6.5Z" />
          <path d="M12 13.5V21" />
          <path d="M12 18c-2 0-3.5-1-4-2.5" />
        </svg>
      );
    case "jewellery":
      return (
        <svg {...common}>
          <path d="M6 4h12l4 5-10 11L2 9l4-5Z" />
          <path d="M2 9h20" />
          <path d="M12 20 8 9l4-5 4 5-4 11Z" />
        </svg>
      );
    case "watch":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="5" />
          <path d="M12 9.5V12l1.5 1.5" />
          <path d="M9.5 7.5 10 3h4l.5 4.5" />
          <path d="M9.5 16.5 10 21h4l.5-4.5" />
        </svg>
      );
    case "chocolate":
      return (
        <svg {...common}>
          <rect x="5" y="4" width="14" height="16" rx="2" />
          <path d="M5 10h14" />
          <path d="M5 15h14" />
          <path d="M12 4v16" />
        </svg>
      );
    case "fragrance":
      return (
        <svg {...common}>
          <path d="M9 3h6v3H9z" />
          <path d="M10 6v2l-3 3v9a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-9l-3-3V6" />
          <path d="M9 14h6" />
        </svg>
      );
    case "apparel":
      return (
        <svg {...common}>
          <path d="m8 4 4 2 4-2 5 4-2.5 3.5L16 10v10H8V10L5.5 11.5 3 8l5-4Z" />
        </svg>
      );
    case "toys":
      return (
        <svg {...common}>
          <path d="M12 3l2.6 5.3 5.9.8-4.2 4.1 1 5.8-5.3-2.8-5.3 2.8 1-5.8-4.2-4.1 5.9-.8L12 3Z" />
        </svg>
      );
    case "decor":
      return (
        <svg {...common}>
          <path d="M7 20h10" />
          <path d="M12 20v-8" />
          <path d="M12 12C8.5 12 6 9.5 6 6c3.5 0 6 2.5 6 6Z" />
          <path d="M12 14c3.5 0 6-2.5 6-6-3.5 0-6 2.5-6 6Z" />
        </svg>
      );
    case "stationery":
      return (
        <svg {...common}>
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          <rect x="3" y="8" width="18" height="4" rx="1" />
          <path d="M12 8v13" />
          <path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7" />
          <path d="M7.5 8a2.5 2.5 0 0 1 0-5C10 3 12 8 12 8s2-5 4.5-5a2.5 2.5 0 0 1 0 5" />
        </svg>
      );
  }
}

export default function CategoryFallbackVisual({ product }) {
  const theme = resolveVisualTheme(product);

  return (
    <div
      className="image-fallback"
      style={{ background: theme.bg }}
      role="img"
      aria-label={`${product.name} (${theme.label})`}
    >
      <div className="fallback-icon-badge" style={{ borderColor: `${theme.accent}33` }}>
        <CategoryIcon themeKey={theme.key} color={theme.accent} />
      </div>
      <span className="fallback-theme-label" style={{ color: theme.accent }}>
        {theme.label}
      </span>
      <span className="fallback-status-note">Image Unavailable</span>
    </div>
  );
}
