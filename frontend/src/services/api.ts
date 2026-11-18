const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "/api").replace(/\/+$/, "");

const ACCESS_KEY = "leave-tracker.access";
const REFRESH_KEY = "leave-tracker.refresh";

export const AUTH_EXPIRED_EVENT = "leave-tracker:auth-expired";

export class ApiError extends Error {
  status: number;
  fieldErrors: Record<string, string>;

  constructor(status: number, message: string, fieldErrors: Record<string, string> = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

export function getAccessToken(): string | null {
  return window.localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return window.localStorage.getItem(REFRESH_KEY);
}

export function setTokens(access: string, refresh?: string): void {
  window.localStorage.setItem(ACCESS_KEY, access);
  if (refresh) {
    window.localStorage.setItem(REFRESH_KEY, refresh);
  }
}

export function clearTokens(): void {
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
}

function buildUrl(path: string): string {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${cleanPath}`;
}

export function buildQuery(params: Record<string, string | number | boolean | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

function parseErrorBody(status: number, body: unknown): ApiError {
  if (body && typeof body === "object" && !Array.isArray(body)) {
    const record = body as Record<string, unknown>;
    if (typeof record.detail === "string") {
      return new ApiError(status, record.detail);
    }
    const fieldErrors: Record<string, string> = {};
    for (const [field, messages] of Object.entries(record)) {
      if (Array.isArray(messages) && messages.length > 0) {
        fieldErrors[field] = String(messages[0]);
      } else if (typeof messages === "string") {
        fieldErrors[field] = messages;
      }
    }
    const first = Object.entries(fieldErrors)[0];
    const message = first ? `${first[0]}: ${first[1]}` : "The request could not be completed.";
    return new ApiError(status, message, fieldErrors);
  }
  return new ApiError(status, "The request could not be completed.");
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) {
    return false;
  }
  const response = await fetch(buildUrl("/auth/refresh/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) {
    return false;
  }
  const data = (await response.json()) as { access: string; refresh?: string };
  setTokens(data.access, data.refresh);
  return true;
}

export async function request<T>(path: string, init: RequestInit = {}, allowRetry = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = getAccessToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(buildUrl(path), { ...init, headers });

  const isAuthCall = path === "/auth/refresh/" || path === "/auth/login/";
  if (response.status === 401 && allowRetry && !isAuthCall) {
    const refreshed = await refreshAccessToken().catch(() => false);
    if (refreshed) {
      return request<T>(path, init, false);
    }
    clearTokens();
    window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  const body: unknown = text ? JSON.parse(text) : null;

  if (!response.ok) {
    throw parseErrorBody(response.status, body);
  }
  return body as T;
}

export function jsonBody(data: unknown): string {
  return JSON.stringify(data);
}
