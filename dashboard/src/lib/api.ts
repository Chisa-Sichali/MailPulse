const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

type Tokens = {
  access_token: string;
  refresh_token: string;
};

function getTokens(): Tokens | null {
  const raw = localStorage.getItem("mailpulse_tokens");
  return raw ? JSON.parse(raw) : null;
}

export function setTokens(tokens: Tokens) {
  localStorage.setItem("mailpulse_tokens", JSON.stringify(tokens));
}

export function clearTokens() {
  localStorage.removeItem("mailpulse_tokens");
}

export function isAuthenticated() {
  return Boolean(getTokens()?.access_token);
}

async function refreshAccessToken(): Promise<string | null> {
  const tokens = getTokens();
  if (!tokens?.refresh_token) return null;

  const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: tokens.refresh_token }),
  });

  if (!res.ok) {
    clearTokens();
    return null;
  }

  const data = await res.json();
  setTokens(data);
  return data.access_token;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const tokens = getTokens();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (tokens?.access_token) {
    headers.set("Authorization", `Bearer ${tokens.access_token}`);
  }

  let response = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (response.status === 401 && tokens?.refresh_token) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers.set("Authorization", `Bearer ${newToken}`);
      response = await fetch(`${API_URL}${path}`, { ...options, headers });
    }
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error?.error?.message || `Request failed (${response.status})`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const authApi = {
  login: (email: string, password: string) =>
    apiFetch<Tokens>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string, full_name?: string) =>
    apiFetch<Tokens>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),
  me: () => apiFetch<{ email: string; full_name: string | null }>("/api/v1/auth/me"),
};

export { API_URL };
