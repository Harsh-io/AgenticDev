/**
 * Utility functions for frontend API error parsing and formatting.
 */

export async function parseApiError(response) {
  let errorMessage = `HTTP error ${response.status}: ${response.statusText}`;
  try {
    const errorBody = await response.json();
    if (errorBody && errorBody.error) {
      errorMessage = errorBody.error;
    } else if (errorBody && errorBody.detail) {
      errorMessage = typeof errorBody.detail === "string" ? errorBody.detail : JSON.stringify(errorBody.detail);
    }
  } catch {
    // Non-JSON response, fallback to default status text
  }
  return new Error(errorMessage);
}

