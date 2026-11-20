/**
 * Frontend environment configuration and runtime URL validation.
 */

export const API_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";

export function validateEnvironment() {
  if (!API_URL) {
    console.warn("[AgenticDev] VITE_API_URL is unset, falling back to http://localhost:8000");
  }
  return {
    apiUrl: API_URL,
    isLocal: API_URL.includes("localhost") || API_URL.includes("127.0.0.1"),
  };
}

