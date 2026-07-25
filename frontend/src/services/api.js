import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});


// ─── Demo Mode Interceptor: route to /demo endpoints ──────────
api.interceptors.request.use(
  (config) => {
    try {
      const isDemo = localStorage.getItem("crimeai_demo_mode") === "true";
      if (isDemo && config.url && !config.url.includes("/auth/") && !config.url.includes("/demo/")) {
        // Map production paths to demo endpoints
        const DEMO_MAP = [
          { from: "/firs/statistics", to: "/demo/firs/statistics" },
          { from: "/firs", to: "/demo/firs" },
          { from: "/victims", to: "/demo/victims" },
          { from: "/accused", to: "/demo/accused" },
          { from: "/evidence", to: "/demo/evidence" },
          { from: "/financial", to: "/demo/transactions" },
          { from: "/hotspots/map", to: "/demo/hotspots/map" },
          { from: "/hotspots", to: "/demo/hotspots" },
          { from: "/network", to: "/demo/network" },
          { from: "/predictions", to: "/demo/predictions" },
          { from: "/users", to: "/demo/users" },
          { from: "/audit-logs", to: "/demo/audit-logs" },
          { from: "/settings", to: "/demo/settings" },
          { from: "/dashboard", to: "/demo/dashboard" },
          { from: "/history", to: "/demo/history" },
        ];
        for (const { from, to } of DEMO_MAP) {
          if (config.url.startsWith(from)) {
            config.url = config.url.replace(from, to);
            break;
          }
        }
      }
    } catch {}
    return config;
  },
  (error) => Promise.reject(error),
);

// ─── Request interceptor: inject JWT ──────────────────────────
api.interceptors.request.use(
  (config) => {
    const stored = localStorage.getItem("crimeai_tokens");
    if (stored) {
      try {
        const tokens = JSON.parse(stored);
        if (tokens.access_token) {
          config.headers.Authorization = `Bearer ${tokens.access_token}`;
        }
      } catch {
        // Corrupted tokens – ignore
      }
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ─── Response interceptor: handle 401 ─────────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retrying and has refresh token
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/auth/")
    ) {
      originalRequest._retry = true;
      const stored = localStorage.getItem("crimeai_tokens");
      if (stored) {
        try {
          const tokens = JSON.parse(stored);
          if (tokens.refresh_token) {
            // Try refreshing the token
            const resp = await api.post(
              "/auth/refresh",
              { refresh_token: tokens.refresh_token },
            );
            const newTokens = resp.data.tokens;
            localStorage.setItem("crimeai_tokens", JSON.stringify(newTokens));
            originalRequest.headers.Authorization = `Bearer ${newTokens.access_token}`;
            return api(originalRequest);
          }
        } catch {
          // Refresh failed – clear auth
          localStorage.removeItem("crimeai_tokens");
          localStorage.removeItem("crimeai_user");
          window.location.href = "/";
        }
      }
    }
    return Promise.reject(error);
  },
);

export default api;
