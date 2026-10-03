"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "./auth-provider";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading, devMode } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !devMode && !user) router.replace("/login");
  }, [user, loading, devMode, router]);

  if (loading) return <div className="center-page">Loading…</div>;
  if (!devMode && !user) return null;
  return <>{children}</>;
}
