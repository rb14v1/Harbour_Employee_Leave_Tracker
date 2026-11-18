import type { AuthConfig, User } from "../types";
import { clearTokens, getRefreshToken, jsonBody, request, setTokens } from "./api";

interface TokenResponse {
  access: string;
  refresh: string;
}

export function fetchAuthConfig(): Promise<AuthConfig> {
  return request<AuthConfig>("/auth/config/");
}

export async function login(username: string, password: string): Promise<void> {
  const tokens = await request<TokenResponse>("/auth/login/", {
    method: "POST",
    body: jsonBody({ username, password }),
  });
  setTokens(tokens.access, tokens.refresh);
}

export async function demoLogin(): Promise<void> {
  const tokens = await request<TokenResponse>("/auth/demo-login/", { method: "POST" });
  setTokens(tokens.access, tokens.refresh);
}

export function fetchCurrentUser(): Promise<User> {
  return request<User>("/auth/me/");
}

export async function logout(): Promise<void> {
  const refresh = getRefreshToken();
  try {
    if (refresh) {
      await request<void>("/auth/logout/", {
        method: "POST",
        body: jsonBody({ refresh }),
      });
    }
  } finally {
    clearTokens();
  }
}
