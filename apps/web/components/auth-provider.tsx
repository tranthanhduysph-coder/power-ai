"use client";

import { onAuthStateChanged, type User } from "firebase/auth";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { auth } from "@/lib/firebase";

const DEV_MODE = process.env.NEXT_PUBLIC_AUTH_MODE === "dev";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  devMode: boolean;
};

const AuthContext = createContext<AuthContextValue>({ user: null, loading: true, devMode: DEV_MODE });

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(!DEV_MODE);

  useEffect(() => {
    if (DEV_MODE) return;
    return onAuthStateChanged(auth, (next) => {
      setUser(next);
      setLoading(false);
    });
  }, []);

  const value = useMemo(() => ({ user, loading, devMode: DEV_MODE }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
