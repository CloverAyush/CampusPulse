"use client";

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { api, ApiError } from "./api";
import { User, UserRole } from "./types";

interface AuthContextValue {
  user: User | null;
  status: "loading" | "authenticated" | "anonymous";
  login: (email: string, password: string) => Promise<User>;
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    department?: string;
  }) => Promise<User>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading");
  const router = useRouter();

  const refresh = useCallback(async () => {
    try {
      const current = await api.getMe();
      setUser(current);
      setStatus("authenticated");
    } catch (error) {
      if (!(error instanceof ApiError) || error.isAuthError) {
        api.clearToken();
        setUser(null);
        setStatus("anonymous");
      } else {
        // The API is reachable but unhappy for another reason. Keep the session and
        // let the page surface the failure rather than silently signing the user out.
        setStatus(user ? "authenticated" : "anonymous");
      }
    }
  }, [user]);

  useEffect(() => {
    // In development, React Strict Mode runs this effect twice on mount (mount,
    // cleanup, mount) to surface exactly this kind of bug: an earlier version of
    // this guard used a ref to skip the second run, which meant the *only* fetch
    // ever made got cancelled by the first run's cleanup and nothing replaced it —
    // `status` stayed "loading" forever. Letting the effect run normally means the
    // second mount simply starts its own fetch, which resolves fine. One extra
    // request in dev only; production never double-invokes.
    let cancelled = false;
    api
      .getMe()
      .then((current) => {
        if (cancelled) return;
        setUser(current);
        setStatus("authenticated");
      })
      .catch(() => {
        if (cancelled) return;
        api.clearToken();
        setUser(null);
        setStatus("anonymous");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    api.setSessionExpiredHandler(() => {
      setUser(null);
      setStatus("anonymous");
      router.replace("/login?expired=1");
    });
    return () => api.setSessionExpiredHandler(null);
  }, [router]);

  const login = useCallback(async (email: string, password: string) => {
    const result = await api.login(email, password);
    setUser(result.user);
    setStatus("authenticated");
    return result.user;
  }, []);

  const register = useCallback(
    async (data: { email: string; password: string; full_name: string; department?: string }) => {
      const result = await api.register(data);
      setUser(result.user);
      setStatus("authenticated");
      return result.user;
    },
    []
  );

  const logout = useCallback(() => {
    api.clearToken();
    setUser(null);
    setStatus("anonymous");
    router.replace("/login");
  }, [router]);

  const value = useMemo(
    () => ({ user, status, login, register, logout, refresh }),
    [user, status, login, register, logout, refresh]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}

export function hasRole(user: User | null, ...roles: UserRole[]): boolean {
  return user !== null && roles.includes(user.role);
}

export const ROLE_LABELS: Record<UserRole, string> = {
  student: "Student",
  handler: "Handler",
  higher_authority: "Higher authority",
  admin: "Administrator",
};

export const ROLE_HOME: Record<UserRole, string> = {
  student: "/my-reports",
  handler: "/handler",
  higher_authority: "/higher-authority",
  admin: "/admin",
};
