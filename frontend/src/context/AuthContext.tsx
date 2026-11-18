import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { AUTH_EXPIRED_EVENT, clearTokens, getAccessToken } from "../services/api";
import {
  demoLogin as demoLoginRequest,
  fetchAuthConfig,
  fetchCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
} from "../services/auth";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  demoMode: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function startDemoSession(): Promise<User> {
  await demoLoginRequest();
  return fetchCurrentUser();
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [demoMode, setDemoMode] = useState<boolean>(false);

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      const config = await fetchAuthConfig().catch(() => ({ demo_mode: false }));
      if (active) {
        setDemoMode(config.demo_mode);
      }

      if (getAccessToken()) {
        try {
          const current = await fetchCurrentUser();
          if (active) setUser(current);
          return;
        } catch {
          clearTokens();
        }
      }

      if (config.demo_mode) {
        const current = await startDemoSession();
        if (active) setUser(current);
      }
    }

    restoreSession()
      .catch(() => {
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const handleExpired = () => {
      if (!demoMode) {
        setUser(null);
        return;
      }
      startDemoSession()
        .then(setUser)
        .catch(() => setUser(null));
    };
    window.addEventListener(AUTH_EXPIRED_EVENT, handleExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handleExpired);
  }, [demoMode]);

  const login = useCallback(async (username: string, password: string) => {
    await loginRequest(username, password);
    setUser(await fetchCurrentUser());
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } finally {
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({ user, loading, demoMode, login, logout }),
    [user, loading, demoMode, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
