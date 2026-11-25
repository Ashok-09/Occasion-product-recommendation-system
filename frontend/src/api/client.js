/**
 * HTTP client helpers for communicating with the FastAPI recommendation backend.
 * In development, Vite proxies `/api/*` requests to `http://127.0.0.1:8000`.
 */

const API_BASE = "/api";

async function parseErrorMessage(response) {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") {
      return body.detail;
    }
    if (Array.isArray(body?.detail) && body.detail.length > 0) {
      return body.detail[0]?.msg || "Invalid request input.";
    }
  } catch {
    // Ignore JSON parsing failures for non-JSON error pages.
  }
  return `Request failed with status ${response.status}.`;
}

export async function fetchOccasions() {
  const response = await fetch(`${API_BASE}/occasions`);
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }
  const data = await response.json();
  return Array.isArray(data.occasions) ? data.occasions : [];
}

export async function fetchRecommendations(occasion, topK = 12) {
  const response = await fetch(`${API_BASE}/recommend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ occasion, top_k: topK }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}
