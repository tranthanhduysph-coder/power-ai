"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { useLanguage } from "@/components/language-provider";
import { useAuth } from "@/components/auth-provider";
import { apiFetch } from "@/lib/api";

export default function DashboardPage() {
  const { language } = useLanguage();
  const { user, devMode, loading } = useAuth();
  const [me, setMe] = useState<any>(null);
  const [progress, setProgress] = useState<any>(null);

  useEffect(() => {
    if (loading || (!devMode && !user)) return;
    Promise.all([apiFetch<any>("/me"), apiFetch<any>("/progress")])
      .then(([m, p]) => { setMe(m); setProgress(p); })
      .catch(console.error);
  }, [user, devMode, loading]);

  const accuracy = progress ? Math.round(progress.summary.mean_accuracy * 100) : 0;
  return (
    <AuthGuard>
      <AppShell>
        <div className="page-heading">
          <div><p className="eyebrow">POWER Biology</p><h1>{language === "vi" ? `Chào ${me?.display_name || "bạn"}` : `Welcome ${me?.display_name || "back"}`}</h1></div>
        </div>
        <section className="hero-card">
          <div>
            <span className="pill">Biology 10</span>
            <h2>{language === "vi" ? "Tiếp tục: Tái bản DNA" : "Continue: DNA replication"}</h2>
            <p>{language === "vi" ? "Một vertical slice hoàn chỉnh để kiểm thử POWER, Tutor và Practice." : "A complete vertical slice for testing POWER, Tutor and Practice."}</p>
            <Link className="button primary inline" href="/learn/dna-replication">{language === "vi" ? "Tiếp tục học" : "Continue learning"}</Link>
          </div>
          <div className="hero-score"><strong>{accuracy}%</strong><span>{language === "vi" ? "Độ chính xác luyện tập" : "Practice accuracy"}</span></div>
        </section>
        <div className="grid-3">
          <div className="stat-card"><span>{language === "vi" ? "Bộ đề hoàn thành" : "Completed sets"}</span><strong>{progress?.summary.completed_sets ?? 0}</strong></div>
          <div className="stat-card"><span>{language === "vi" ? "Khái niệm đã đo" : "Measured concepts"}</span><strong>{progress?.concepts.length ?? 0}</strong></div>
          <div className="stat-card"><span>{language === "vi" ? "Gợi ý tiếp theo" : "Next action"}</span><Link href="/practice">{language === "vi" ? "Luyện tập thích ứng →" : "Adaptive practice →"}</Link></div>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
