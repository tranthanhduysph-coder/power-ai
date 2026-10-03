"use client";

import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { useLanguage } from "@/components/language-provider";
import { TutorRenderer } from "@/components/tutor-renderer";
import { apiFetch } from "@/lib/api";
import type { TutorBlock } from "@/lib/types";

const phases = ["PREPARE", "ORGANIZE", "WORK", "EVALUATE", "RETHINK"] as const;

export default function LearnPage() {
  const { language } = useLanguage();
  const [powerId, setPowerId] = useState<string | null>(null);
  const [phase, setPhase] = useState<(typeof phases)[number]>("PREPARE");
  const [goal, setGoal] = useState("");
  const [message, setMessage] = useState("");
  const [blocks, setBlocks] = useState<TutorBlock[]>([]);
  const [busy, setBusy] = useState(false);

  const ensureSession = async () => {
    if (powerId) return powerId;
    const res = await apiFetch<{ id: string }>("/power/sessions", {
      method: "POST",
      body: JSON.stringify({ unit_code: "B12_DNA_REPLICATION", language }),
    });
    setPowerId(res.id);
    return res.id;
  };

  const completePhase = async () => {
    const id = await ensureSession();
    const state = phase === "PREPARE" ? { goal: goal || "Understand DNA replication", confidence: 3 } : { note: `${phase} completed` };
    const res = await apiFetch<{ current_phase: (typeof phases)[number] }>(`/power/sessions/${id}/phase`, {
      method: "PUT",
      body: JSON.stringify({ phase, state, completed: true }),
    });
    setPhase(res.current_phase);
  };

  const askTutor = async () => {
    if (!message.trim()) return;
    setBusy(true);
    try {
      const res = await apiFetch<{ blocks: TutorBlock[] }>("/tutor/respond", {
        method: "POST",
        body: JSON.stringify({ concept_code: "BIO.DNA.REPLICATION", message, language }),
      });
      setBlocks(res.blocks);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthGuard>
      <AppShell>
        <div className="page-heading"><div><p className="eyebrow">Biology 12 · Molecular genetics</p><h1>{language === "vi" ? "Tái bản DNA" : "DNA replication"}</h1></div></div>
        <div className="power-stepper">
          {phases.map((p) => <div key={p} className={p === phase ? "power-step active" : "power-step"}>{p[0]}<span>{p}</span></div>)}
        </div>
        <div className="lesson-layout">
          <article className="lesson-card">
            <h2>{language === "vi" ? "Vì sao có mạch dẫn đầu và mạch chậm?" : "Why are there leading and lagging strands?"}</h2>
            <p>{language === "vi" ? "Hai mạch DNA ngược chiều nhau. DNA polymerase chỉ kéo dài mạch mới theo chiều 5′→3′. Vì vậy tại một chạc tái bản, một mạch mới có thể được tổng hợp liên tục, trong khi mạch còn lại phải tạo thành các đoạn ngắn rồi nối lại." : "The two DNA templates are antiparallel. DNA polymerase extends new DNA only 5′→3′. At a replication fork, one new strand can therefore be synthesized continuously while the other must be synthesized as short segments that are later joined."}</p>
            <div className="concept-visual">
              <div>5′ ─────────────── 3′</div>
              <div className="fork-line">↘ {language === "vi" ? "Mạch dẫn đầu" : "Leading strand"}</div>
              <div className="fork-line">↗ {language === "vi" ? "Mạch chậm · Okazaki" : "Lagging strand · Okazaki"}</div>
              <div>3′ ─────────────── 5′</div>
            </div>
            {phase === "PREPARE" && <label className="field-block"><span>{language === "vi" ? "Mục tiêu học tập của bạn" : "Your learning goal"}</span><textarea value={goal} onChange={(e) => setGoal(e.target.value)} placeholder={language === "vi" ? "Ví dụ: giải thích được vì sao mạch chậm cần các đoạn Okazaki" : "Example: explain why the lagging strand requires Okazaki fragments"} /></label>}
            <button className="button primary inline" onClick={completePhase}>{language === "vi" ? `Hoàn thành ${phase}` : `Complete ${phase}`}</button>
          </article>
          <aside className="tutor-card">
            <div className="tutor-header"><div><span className="pill">POWER Tutor</span><h3>{language === "vi" ? "Hỏi trong ngữ cảnh bài học" : "Ask in lesson context"}</h3></div></div>
            <div className="quick-actions">
              {[language === "vi" ? "Giải thích đơn giản hơn" : "Explain more simply", language === "vi" ? "So sánh hai mạch" : "Compare the two strands", language === "vi" ? "Kiểm tra tôi" : "Quiz me"].map((x) => <button key={x} onClick={() => setMessage(x)}>{x}</button>)}
            </div>
            {blocks.length > 0 && <TutorRenderer blocks={blocks} />}
            <div className="tutor-input"><textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder={language === "vi" ? "Hỏi POWER về phần này…" : "Ask POWER about this…"}/><button className="button primary" disabled={busy} onClick={askTutor}>{busy ? "…" : (language === "vi" ? "Gửi" : "Send")}</button></div>
          </aside>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
