"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

type ServiceState = "checking" | "ready" | "offline" | "api_down" | "not_ready";

export function ServiceStatusBanner() {
  const [state, setState] = useState<ServiceState>("checking");

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setInterval> | null = null;

    const check = async () => {
      if (!navigator.onLine) {
        if (!cancelled) setState("offline");
        return;
      }
      try {
        const response = await fetch(`${API_URL}/health/ready`, { cache: "no-store" });
        if (!cancelled) setState(response.ok ? "ready" : "not_ready");
      } catch {
        if (!cancelled) setState("api_down");
      }
    };

    const onOnline = () => check();
    const onOffline = () => setState("offline");
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    check();
    timer = setInterval(check, 30000);

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, []);

  if (state === "ready" || state === "checking") return null;

  const message = state === "offline"
    ? "Thiết bị đang mất kết nối mạng. Dữ liệu mới chưa thể đồng bộ."
    : state === "api_down"
      ? "POWER API chưa kết nối. Hãy kiểm tra FastAPI ở localhost:8000."
      : "POWER API đang chạy nhưng database chưa sẵn sàng. Hãy chạy migration/seed và kiểm tra /health/ready.";

  return <div className="service-status-banner" role="status"><strong>POWER local:</strong> {message}</div>;
}
