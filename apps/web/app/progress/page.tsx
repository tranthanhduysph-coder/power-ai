"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { useLanguage } from "@/components/language-provider";
import { useAuth } from "@/components/auth-provider";
import { apiFetch } from "@/lib/api";

export default function ProgressPage() {
  const { language } = useLanguage();
  const { user, devMode, loading } = useAuth();
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    if (loading || (!devMode && !user)) return;
    apiFetch<any>("/progress").then(setData).catch(console.error);
  }, [user, devMode, loading]);
  return (
    <AuthGuard><AppShell>
      <div className="page-heading"><div><p className="eyebrow">Learner Model</p><h1>{language === "vi" ? "Tiến trình" : "Progress"}</h1></div></div>
      <div className="grid-2">
        <div className="stat-card"><span>{language === "vi" ? "Bộ đề hoàn thành" : "Completed sets"}</span><strong>{data?.summary.completed_sets ?? 0}</strong></div>
        <div className="stat-card"><span>{language === "vi" ? "Độ chính xác trung bình" : "Mean accuracy"}</span><strong>{Math.round((data?.summary.mean_accuracy ?? 0) * 100)}%</strong></div>
      </div>
      <section className="card mastery-card"><h2>{language === "vi" ? "Mức độ thành thạo theo khái niệm" : "Concept mastery"}</h2>
        {!data?.concepts?.length && <p className="muted">{language === "vi" ? "Hãy hoàn thành một bộ luyện tập để bắt đầu xây learner model." : "Complete a practice set to start building your learner model."}</p>}
        {data?.concepts?.map((c:any) => <div className="mastery-row" key={c.code}><div><strong>{language === "vi" ? c.name_vi : c.name_en}</strong><small>{c.attempt_count} {language === "vi" ? "lượt" : "attempts"}</small></div><div className="mastery-bar"><span style={{width:`${Math.round(Number(c.mastery_score)*100)}%`}} /></div><strong>{Math.round(Number(c.mastery_score)*100)}%</strong></div>)}
      </section>
    </AppShell></AuthGuard>
  );
}
