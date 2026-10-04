"use client";

import { onAuthStateChanged, type User } from "firebase/auth";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { auth } from "@/lib/firebase";

const DEV_MODE = process.env.NEXT_PUBLIC_AUTH_MODE === "dev";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  devMode: boolean;
  error: string | null;
};

const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  devMode: DEV_MODE,
  error: null,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(!DEV_MODE);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (DEV_MODE) {
      setLoading(false);
      return;
    }
    return onAuthStateChanged(
      auth,
      (next) => {
        setUser(next);
        setError(null);
        setLoading(false);
      },
      (authError) => {
        setError(authError?.message || "Firebase Authentication is unavailable.");
        setLoading(false);
      }
    );
  }, []);

  const value = useMemo(
    () => ({ user, loading, devMode: DEV_MODE, error }),
    [user, loading, error]
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
