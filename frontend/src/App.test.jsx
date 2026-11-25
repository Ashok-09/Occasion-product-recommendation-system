import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App.jsx";

function createJsonResponse(payload, ok = true, status = 200) {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(payload),
  });
}

describe("Occasion-Based Product Recommendation UI", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loads occasion chips and renders ranked product cards below input", async () => {
    fetch.mockImplementation((url) => {
      if (url.includes("/api/occasions")) {
        return createJsonResponse({ occasions: ["Birthday", "Diwali"] });
      }
      if (url.includes("/api/recommend")) {
        return createJsonResponse({
          occasion: "Diwali",
          total_results: 1,
          message: "Found 1 recommended products for 'Diwali'.",
          recommendations: [
            {
              product_id: "p-1",
              vendor_id: "v-1",
              category_id: "cat-1234567890",
              name: "Diwali Dry fruits hampers",
              brand: "Joy of Giving",
              description: "Thoughtfully curated dry fruits hamper for Diwali.",
              image: "https://example.com/hamper.png",
              files: ["https://example.com/hamper.png"],
              price: 1999,
              discount_percentage: 5,
              discounted_price: 1899.05,
              stock: 70,
              score: 0.864,
              reason: "Matches 'diwali', 'dry fruits' in product name and description.",
            },
          ],
        });
      }
      return createJsonResponse({}, false, 404);
    });

    render(<App />);

    const input = screen.getByLabelText(/What occasion are you shopping for/i);
    fireEvent.change(input, { target: { value: "Diwali" } });
    fireEvent.click(screen.getByRole("button", { name: /Find Recommendations/i }));

    await waitFor(() => {
      expect(screen.getByText(/Recommended for "Diwali"/i)).toBeInTheDocument();
    });

    expect(screen.getByText("Diwali Dry fruits hampers")).toBeInTheDocument();
    expect(screen.getByText("Joy of Giving")).toBeInTheDocument();
    expect(screen.getByText("86% match")).toBeInTheDocument();
    expect(screen.getByText(/Matches 'diwali', 'dry fruits'/i)).toBeInTheDocument();

    // Verify broken image URL gracefully swaps to Image Unavailable fallback.
    const img = screen.getByRole("img", { name: "Diwali Dry fruits hampers" });
    fireEvent.error(img);
    expect(screen.getByText("Image Unavailable")).toBeInTheDocument();
  });

  it("shows validation error on blank submit and loading + empty state on unknown occasion", async () => {
    let resolveRecommend;
    fetch.mockImplementation((url) => {
      if (url.includes("/api/occasions")) {
        return createJsonResponse({ occasions: ["Birthday"] });
      }
      if (url.includes("/api/recommend")) {
        return new Promise((resolve) => {
          resolveRecommend = resolve;
        });
      }
      return createJsonResponse({}, false, 404);
    });

    render(<App />);

    // Blank submission validation
    fireEvent.click(screen.getByRole("button", { name: /Find Recommendations/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(/Please enter an occasion/i);

    // Loading state followed by empty state
    const input = screen.getByLabelText(/What occasion are you shopping for/i);
    fireEvent.change(input, { target: { value: "xyz123" } });
    fireEvent.click(screen.getByRole("button", { name: /Find Recommendations/i }));

    expect(screen.getByText(/Analyzing catalog for "xyz123"/i)).toBeInTheDocument();

    resolveRecommend({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          occasion: "xyz123",
          total_results: 0,
          recommendations: [],
          message: "No strong matches found for 'xyz123'.",
        }),
    });

    await waitFor(() => {
      expect(screen.getByText(/No matching products found for "xyz123"/i)).toBeInTheDocument();
    });
  });

  it("displays an error alert when the backend request fails", async () => {
    fetch.mockImplementation((url) => {
      if (url.includes("/api/occasions")) {
        return createJsonResponse({ occasions: ["Birthday"] });
      }
      return createJsonResponse({ detail: "Product catalog is not ready." }, false, 503);
    });

    render(<App />);
    const input = screen.getByLabelText(/What occasion are you shopping for/i);
    fireEvent.change(input, { target: { value: "Birthday" } });
    fireEvent.click(screen.getByRole("button", { name: /Find Recommendations/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Product catalog is not ready.");
    });
  });
});
