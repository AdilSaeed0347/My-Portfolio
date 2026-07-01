// frontend/config.js
// This is the SINGLE place where backend URL is configured.
// In production, window.__ENV__.BACKEND_URL is injected by the server.
// In development, it falls back to localhost automatically.

(function () {
  var backendUrl =
    (window.__ENV__ && window.__ENV__.BACKEND_URL) ||
    "http://127.0.0.1:8000";

  window.CONFIG = {
    BACKEND_URL: backendUrl,
    TIMEOUT_MS: 30000,
    MAX_RETRIES: 2,
  };

  if (backendUrl.includes("127.0.0.1") || backendUrl.includes("localhost")) {
    console.warn("⚠️  Running in development mode — using localhost backend.");
  }
})();