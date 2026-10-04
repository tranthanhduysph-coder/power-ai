"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "./auth-provider";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading, devMode, error } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !devMode && !user && !error) router.replace("/login");
  }, [user, loading, devMode, error, router]);

  if (loading) return <div className="center-page"><div className="status-panel">Đang kiểm tra phiên đăng nhập…</div></div>;
  if (error) return <div className="center-page"><div className="status-panel status-error"><strong>Không thể kết nối dịch vụ đăng nhập</strong><p>{error}</p><p>Kiểm tra Firebase Auth Emulator ở <code>127.0.0.1:9099</code>, sau đó tải lại trang.</p><button className="button primary" onClick={() => window.location.reload()}>Thử lại</button></div></div>;
  if (!devMode && !user) return null;
  return <>{children}</>;
}
