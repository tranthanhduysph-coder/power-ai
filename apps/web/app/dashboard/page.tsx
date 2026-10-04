"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { useLanguage } from "@/components/language-provider";
import { useAuth } from "@/components/auth-provider";
import { apiFetch } from "@/lib/api";

type Progress = {
  concepts: any[];
  summary: {
    completed_sets: number;
    mean_accuracy: number;
    latest_accuracy: number | null;
    latest_completed_at: string | null;
  };
  active_cycle: null | {
    id: string;
    current_phase: "PREPARE" | "ORGANIZE" | "WORK" | "EVALUATE" | "RETHINK";
    unit_code: string;
    name_vi: string;
    name_en: string;
    grade: number;
    updated_at: string;
  };
  next_recommendation: null | {
    id: string;
    type: string;
    priority: number;
    payload: {
      title?: string;
      reason?: string;
      route?: string;
      weak_concepts?: string[];
    };
    created_at: string;
    unit_code: string | null;
    name_vi: string | null;
    name_en: string | null;
  };
};

export default function DashboardPage() {
  const { language } = useLanguage();
  const { user, devMode, loading } = useAuth();
  const [me, setMe] = useState<any>(null);
  const [progress, setProgress] = useState<Progress | null>(null);

  const loadDashboard = useCallback(async () => {
    if (loading || (!devMode && !user)) return;
    const [m, p] = await Promise.all([
      apiFetch<any>("/me"),
      apiFetch<Progress>("/progress"),
    ]);
    setMe(m);
    setProgress(p);
  }, [user, devMode, loading]);

  useEffect(() => {
    loadDashboard().catch(console.error);

    const refresh = () => loadDashboard().catch(console.error);
    const onVisibility = () => {
      if (document.visibilityState === "visible") refresh();
    };

    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [loadDashboard]);

  const latestAccuracy = progress?.summary.latest_accuracy;
  const latestPercent = latestAccuracy == null ? 0 : Math.round(latestAccuracy * 100);
  const meanPercent = progress ? Math.round(progress.summary.mean_accuracy * 100) : 0;
  const recommendation = progress?.next_recommendation;
  const recommendationTitle = recommendation?.payload?.title || (language === "vi" ? "Luyện tập thích ứng" : "Adaptive practice");
  const recommendationRoute = recommendation?.payload?.route || "/practice";
  const continueRoute = progress?.active_cycle ? `/learn/${encodeURIComponent(progress.active_cycle.unit_code)}` : "/learn";

  return (
    <AuthGuard>
      <AppShell>
        <div className="page-heading">
          <div>
            <p className="eyebrow">POWER Biology</p>
            <h1>{language === "vi" ? `Chào ${me?.display_name || "bạn"}` : `Welcome ${me?.display_name || "back"}`}</h1>
          </div>
        </div>
        <section className="hero-card">
          <div>
            <span className="pill">{language === "vi" ? `Sinh học ${progress?.active_cycle?.grade ?? "10–12"}` : `Biology ${progress?.active_cycle?.grade ?? "10–12"}`} · {progress?.active_cycle?.current_phase ?? "POWER"}</span>
            <h2>{progress?.active_cycle ? (language === "vi" ? `Tiếp tục: ${progress.active_cycle.name_vi}` : `Continue: ${progress.active_cycle.name_en}`) : (language === "vi" ? "Chọn một bài học để bắt đầu chu trình POWER" : "Choose a lesson to start a POWER cycle")}</h2>
            <p>{language === "vi" ? "POWER ghi nhớ bạn đang ở pha nào và tiếp tục đúng vị trí trong chu trình học." : "POWER remembers your current phase and resumes the learning cycle at the right place."}</p>
            <Link className="button primary inline" href={continueRoute}>{progress?.active_cycle ? (language === "vi" ? "Tiếp tục học" : "Continue learning") : (language === "vi" ? "Chọn bài học" : "Choose lesson")}</Link>
          </div>
          <div className="hero-score">
            <strong>{latestPercent}%</strong>
            <span>
              {language === "vi"
                ? `Kết quả gần nhất · TB ${meanPercent}%`
                : `Latest result · Avg ${meanPercent}%`}
            </span>
          </div>
        </section>
        <div className="grid-3">
          <div className="stat-card"><span>{language === "vi" ? "Bộ đề hoàn thành" : "Completed sets"}</span><strong>{progress?.summary.completed_sets ?? 0}</strong></div>
          <div className="stat-card"><span>{language === "vi" ? "Khái niệm đã đo" : "Measured concepts"}</span><strong>{progress?.concepts.length ?? 0}</strong></div>
          <div className="stat-card"><span>{language === "vi" ? "Gợi ý tiếp theo" : "Next action"}</span><Link href={recommendationRoute}>{recommendationTitle} →</Link>{recommendation?.payload?.reason && <small className="muted">{recommendation.payload.reason}</small>}</div>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
