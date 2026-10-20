"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { useLanguage } from "@/components/language-provider";
import { useAuth } from "@/components/auth-provider";
import { apiFetch } from "@/lib/api";

type ProgressData = {
  summary: { completed_sets: number; mean_accuracy: number };
  concepts: { code: string; name_vi: string; name_en: string; attempt_count: number; mastery_score: number }[];
};
type Cycle = {
  id: string; current_phase: string; status: string; created_at: string; updated_at: string; completed_phases: number;
  unit: { code: string; name_vi: string; name_en: string };
};
type HistoryPage = { sessions: Cycle[]; has_more: boolean; next_offset: number | null };

export default function ProgressPage() {
  const { language } = useLanguage();
  const vi = language === "vi";
  const { user, devMode, loading } = useAuth();
  const [data, setData] = useState<ProgressData | null>(null);
  const [cycles, setCycles] = useState<Cycle[]>([]);
  const [nextOffset, setNextOffset] = useState<number | null>(null);
  const [historyBusy, setHistoryBusy] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    if (loading || (!devMode && !user)) return;
    let cancelled = false;
    setData(null);
    setCycles([]);
    setError("");
    setHistoryBusy(true);
    Promise.allSettled([
      apiFetch<ProgressData>("/progress"),
      apiFetch<HistoryPage>("/power/sessions/history?summary=true&limit=20&offset=0"),
    ]).then(([progress, history]) => {
      if (cancelled) return;
      if (progress.status === "fulfilled") setData(progress.value);
      else setError(progress.reason instanceof Error ? progress.reason.message : "Unable to load progress");
      if (history.status === "fulfilled") {
        setCycles(history.value.sessions);
        setNextOffset(history.value.next_offset);
      } else setError(history.reason instanceof Error ? history.reason.message : "Unable to load learning cycles");
      setHistoryBusy(false);
    });
    return () => { cancelled = true; };
  }, [user, devMode, loading]);

  const loadMore = async () => {
    if (nextOffset === null || historyBusy) return;
    setHistoryBusy(true);
    setError("");
    try {
      const page = await apiFetch<HistoryPage>(`/power/sessions/history?summary=true&limit=20&offset=${nextOffset}`);
      setCycles(previous => [...previous, ...page.sessions.filter(cycle => !previous.some(item => item.id === cycle.id))]);
      setNextOffset(page.next_offset);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Unable to load learning cycles");
    } finally { setHistoryBusy(false); }
  };
  const date = (value: string) => new Date(value).toLocaleString(vi ? "vi-VN" : "en-US", { dateStyle: "medium", timeStyle: "short" });

  return <AuthGuard><AppShell>
    <div className="page-heading"><div><p className="eyebrow">POWER learning journey</p><h1>{vi ? "Tiến trình học tập" : "Learning progress"}</h1></div></div>
    {error && <p className="notice-banner error-notice" role="alert">{error}</p>}
    <section id="power-history" className="card power-history-card">
      <h2>{vi ? "Các chu trình POWER của bạn" : "Your POWER cycles"}</h2>
      <p className="muted">{vi ? "Mở một chu trình để tiếp tục học hoặc xem lại mục tiêu, sơ đồ, câu trả lời, kết quả và phản tư ở các pha P–O–W–E–R. Mở chu trình cũ không tạo chu trình mới." : "Open a cycle to continue or review your goal, map, responses, results and reflection across P–O–W–E–R. Opening an old cycle does not create a new one."}</p>
      {!cycles.length && !historyBusy && !error && <p>{vi ? "Bạn chưa có chu trình POWER nào. Chọn một bài học để bắt đầu." : "You have no POWER cycles yet. Choose a lesson to begin."} <Link href="/learn">{vi ? "Mở danh sách bài học" : "Browse lessons"}</Link></p>}
      <div className="power-history-list">{cycles.map(cycle => <article key={cycle.id} className="power-history-item">
        <div><h3>{vi ? cycle.unit.name_vi : cycle.unit.name_en}</h3>
          <p><span className="pill">{cycle.status === "completed" ? (vi ? "Đã hoàn thành" : "Completed") : (vi ? `Đang học · ${cycle.current_phase}` : `In progress · ${cycle.current_phase}`)}</span></p>
          <small>{vi ? "Bắt đầu: " : "Started: "}{date(cycle.created_at)} · {vi ? "Cập nhật: " : "Updated: "}{date(cycle.updated_at)}</small>
          <div className="power-history-completion"><progress max={5} value={cycle.completed_phases} aria-label={vi ? "Số pha đã hoàn thành" : "Completed phases"} /><span>{cycle.completed_phases}/5 {vi ? "pha" : "phases"}</span></div>
        </div>
        <Link className="button secondary inline" href={`/learn/${encodeURIComponent(cycle.unit.code)}?session=${encodeURIComponent(cycle.id)}`}>{cycle.status === "completed" ? (vi ? "Xem lại các pha" : "Review phases") : (vi ? "Tiếp tục chu trình" : "Continue cycle")}</Link>
      </article>)}</div>
      {historyBusy && <p role="status">{vi ? "Đang tải chu trình…" : "Loading cycles…"}</p>}
      {nextOffset !== null && <button type="button" className="button secondary inline" disabled={historyBusy} onClick={loadMore}>{vi ? "Xem thêm chu trình" : "Load more cycles"}</button>}
    </section>
    <div className="grid-2">
      <div className="stat-card"><span>{vi ? "Bộ đề hoàn thành" : "Completed sets"}</span><strong>{data?.summary.completed_sets ?? "—"}</strong></div>
      <div className="stat-card"><span>{vi ? "Độ chính xác trung bình" : "Mean accuracy"}</span><strong>{data ? `${Math.round(data.summary.mean_accuracy * 100)}%` : "—"}</strong></div>
    </div>
    <section className="card mastery-card"><h2>{vi ? "Mức độ thành thạo theo khái niệm" : "Concept mastery"}</h2>
      {data && !data.concepts.length && <p className="muted">{vi ? "Hãy hoàn thành một bộ luyện tập để bắt đầu theo dõi mức độ nắm vững kiến thức." : "Complete a practice set to start tracking concept mastery."}</p>}
      {data?.concepts.map(concept => <div className="mastery-row" key={concept.code}><div><strong>{vi ? concept.name_vi : concept.name_en}</strong><small>{concept.attempt_count} {vi ? "lượt" : "attempts"}</small></div><div className="mastery-bar"><span style={{ width: `${Math.round(Number(concept.mastery_score) * 100)}%` }} /></div><strong>{Math.round(Number(concept.mastery_score) * 100)}%</strong></div>)}
    </section>
  </AppShell></AuthGuard>;
}
