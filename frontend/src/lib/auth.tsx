"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { User, UserRole } from "./types";
import { api } from "./api";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  demoLogin: (role: UserRole) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    try {
      const userData = await api.getMe();
      setUser(userData);
    } catch {
      setUser(null);
      api.clearToken();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Attempt auto login from stored token, or fallback to default student demo if empty
    const token = typeof window !== "undefined" ? localStorage.getItem("campuspulse_token") : null;
    if (token) {
      refreshUser();
    } else {
      // Default to student demo persona for immediate friction-free testing
      api.demoLogin("student").then((res) => {
        setUser(res.user);
        setLoading(false);
      }).catch(() => {
        setLoading(false);
      });
    }
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const res = await api.login(email, password);
      setUser(res.user);
    } finally {
      setLoading(false);
    }
  };

  const demoLogin = async (role: UserRole) => {
    setLoading(true);
    try {
      const res = await api.demoLogin(role);
      setUser(res.user);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    api.clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, demoLogin, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

