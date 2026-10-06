"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { useLanguage } from "@/components/language-provider";
import { useAuth } from "@/components/auth-provider";
import { apiFetch } from "@/lib/api";
import type { PracticeQuestion } from "@/lib/types";


type CatalogUnit = {
  code: string;
  name_vi: string;
  name_en: string;
  grade: number;
  is_power_ready: boolean;
};

type Generated = {
  practice_set_id: string;
  mode: string;
  purpose: "standalone" | "evaluate";
  power_session_id?: string | null;
  unit_code?: string;
  questions: PracticeQuestion[];
};

type EvaluateConcept = {
  concept_code: string;
  name_vi: string;
  name_en: string;
  correct: number;
  total: number;
  accuracy: number;
  mastery: number;
};

type Result = {
  accuracy: number;
  correct: number;
  total: number;
  results: {
    question_id: string;
    is_correct: boolean;
    explanation_vi: string;
    explanation_en: string;
  }[];
  power?: {
    session_id: string;
    current_phase: string;
    evaluate: {
      accuracy: number;
      correct: number;
      total: number;
      concepts: EvaluateConcept[];
      weak_concepts: string[];
    };
  } | null;
};

export default function PracticePage() {
  const { language } = useLanguage();
  const { user, devMode, loading: authLoading } = useAuth();
  const [mode, setMode] = useState<"custom" | "adaptive" | "ai">("adaptive");
  const [difficulty, setDifficulty] = useState("auto");
  const [count, setCount] = useState(6);
  const [types, setTypes] = useState(["mcq", "true_false", "short_answer"]);
  const [generated, setGenerated] = useState<Generated | null>(null);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [result, setResult] = useState<Result | null>(null);
  const [powerSessionId, setPowerSessionId] = useState<string | null>(null);
  const [unitCode, setUnitCode] = useState("B12_DNA_REPLICATION");
  const [readyUnits, setReadyUnits] = useState<CatalogUnit[]>([]);
  const [purpose, setPurpose] = useState<"standalone" | "evaluate">("standalone");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [aiInstruction, setAiInstruction] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("powerSessionId");
    const requestedPurpose = params.get("purpose");
    const requestedUnit = params.get("unitCode");
    if (requestedUnit) setUnitCode(requestedUnit);
    if (sessionId && requestedPurpose === "evaluate") {
      setPowerSessionId(sessionId);
      setPurpose("evaluate");
      setMode("adaptive");
      setCount(6);
    }
  }, []);

  useEffect(() => {
    if (authLoading || (!devMode && !user)) return;
    apiFetch<{ items: CatalogUnit[] }>("/catalog?ready_only=true")
      .then((res) => setReadyUnits(res.items))
      .catch((error) => setNotice(error instanceof Error ? error.message : "Unable to load practice topics"));
  }, [authLoading, devMode, user]);

  const toggleType = (type: string) => setTypes((old) => old.includes(type) ? old.filter((x) => x !== type) : [...old, type]);

  const selectMode = (nextMode: "custom" | "adaptive" | "ai") => {
    if (purpose === "evaluate" && nextMode === "ai") return;
    setMode(nextMode);
    if (nextMode === "adaptive") {
      setDifficulty("auto");
      setCount(6);
      setTypes(["mcq", "true_false", "short_answer"]);
      setAiInstruction("");
    }
  };

  const generate = async () => {
    setBusy(true);
    setNotice(null);
    setResult(null);
    try {
      const res = await apiFetch<Generated>("/practice/generate", {
        method: "POST",
        body: JSON.stringify({
          mode,
          unit_code: unitCode,
          difficulty,
          question_types: types,
          question_count: count,
          power_session_id: purpose === "evaluate" ? powerSessionId : null,
          purpose,
          ai_instruction: mode === "ai" ? aiInstruction.trim() || null : null,
        }),
      });
      if (res.unit_code) setUnitCode(res.unit_code);
      setGenerated(res);
      setAnswers({});
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to generate practice");
    } finally {
      setBusy(false);
    }
  };

  const submit = async () => {
    if (!generated) return;
    setBusy(true);
    setNotice(null);
    try {
      const payload = generated.questions.map((q) => ({
        question_id: q.id,
        answer: answers[q.id] ?? "",
        response_time_ms: null,
        hint_used: false,
      }));
      const res = await apiFetch<Result>(`/practice/${generated.practice_set_id}/submit`, {
        method: "POST",
        body: JSON.stringify({ answers: payload }),
      });
      setResult(res);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to submit practice");
    } finally {
      setBusy(false);
    }
  };

  const evaluateMode = purpose === "evaluate";
  const configLocked = mode === "adaptive";

  return (
    <AuthGuard>
      <AppShell>
        <div className="page-heading">
          <div>
            <p className="eyebrow">{evaluateMode ? "E · POWER Evaluate" : "Practice Engine"}</p>
            <h1>{evaluateMode ? (language === "vi" ? "Đánh giá mức độ hiểu" : "Evaluate understanding") : (language === "vi" ? "Luyện tập" : "Practice")}</h1>
            {evaluateMode && <p className="muted">{language === "vi" ? "Bộ câu hỏi này được gắn trực tiếp với chu trình POWER hiện tại. Khi nộp bài, Evaluate sẽ tự hoàn thành và chuyển sang Rethink." : "This practice set is linked to the current POWER cycle. Submitting it will complete Evaluate and move the cycle to Rethink."}</p>}
          </div>
        </div>

        {notice && <div className="notice-banner">{notice}</div>}

        {!generated && <section className="practice-builder card">
          <div className="mode-grid">
            <button className={mode === "adaptive" ? "mode-card active" : "mode-card"} onClick={() => selectMode("adaptive")}>
              <strong>{language === "vi" ? "Phù hợp với tôi" : "Recommended for me"}</strong>
              <span>{language === "vi" ? "Ưu tiên khái niệm còn yếu dựa trên mastery hiện tại." : "Prioritize weak concepts from current mastery."}</span>
            </button>
            <button className={mode === "custom" ? "mode-card active" : "mode-card"} onClick={() => selectMode("custom")}>
              <strong>{language === "vi" ? "Tự chọn" : "Custom"}</strong>
              <span>{language === "vi" ? "Chọn mức độ và dạng câu hỏi." : "Choose difficulty and question formats."}</span>
            </button>
            <button disabled={evaluateMode} className={mode === "ai" ? "mode-card active" : "mode-card"} onClick={() => selectMode("ai")}>
              <strong>{language === "vi" ? "Tạo bài luyện bằng AI" : "AI-generated practice"}</strong>
              <span>{language === "vi" ? "Tạo bộ luyện mới theo yêu cầu; không dùng để cập nhật mastery hay POWER Evaluate." : "Create a new practice set on demand; it does not update mastery or POWER Evaluate."}</span>
            </button>
          </div>
          <div className="form-grid">
            <label>{language === "vi" ? "Nội dung" : "Topic"}<select value={unitCode} disabled={evaluateMode || configLocked} onChange={(e) => setUnitCode(e.target.value)}>{readyUnits.length > 0 ? readyUnits.map((unit) => <option key={unit.code} value={unit.code}>{language === "vi" ? `Sinh học ${unit.grade} · ${unit.name_vi}` : `Biology ${unit.grade} · ${unit.name_en}`}</option>) : <option value={unitCode}>{unitCode}</option>}</select></label>
            <label>{language === "vi" ? "Mức độ khó" : "Difficulty"}<select value={difficulty} disabled={configLocked} onChange={(e) => setDifficulty(e.target.value)}><option value="auto">Adaptive / Auto</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
            <label>{language === "vi" ? "Số câu" : "Questions"}<select value={count} disabled={configLocked} onChange={(e) => setCount(Number(e.target.value))}><option>3</option><option>6</option><option>9</option><option>12</option></select></label>
          </div>
          <div className="check-row">
            {[["mcq", language === "vi" ? "Trắc nghiệm" : "Multiple choice"], ["true_false", language === "vi" ? "Đúng/Sai" : "True/False"], ["short_answer", language === "vi" ? "Trả lời ngắn" : "Short answer"]].map(([value, label]) => <label key={value}><input type="checkbox" disabled={configLocked} checked={types.includes(value)} onChange={() => toggleType(value)} /> {label}</label>)}
          </div>
          {mode === "ai" && <label className="field-block">
            <span>{language === "vi" ? "Yêu cầu cho AI (không bắt buộc)" : "Instructions for AI (optional)"}</span>
            <textarea value={aiInstruction} maxLength={800} onChange={(e) => setAiInstruction(e.target.value)} placeholder={language === "vi" ? "Ví dụ: tập trung vào operon Lac, ưu tiên câu vận dụng và tránh câu hỏi ghi nhớ đơn thuần." : "Example: focus on the lac operon, emphasize application, and avoid simple recall questions."} />
          </label>}
          <button className="button primary inline" disabled={types.length === 0 || busy} onClick={generate}>{busy ? "…" : (evaluateMode ? (language === "vi" ? "Tạo bộ đánh giá" : "Generate evaluation") : (language === "vi" ? "Tạo bài luyện" : "Generate practice"))}</button>
        </section>}

        {generated && <section className="question-list">
          <div className="section-toolbar"><strong>{generated.questions.length} {language === "vi" ? "câu hỏi" : "questions"}</strong>{!result && <button className="text-button" onClick={() => setGenerated(null)}>{language === "vi" ? "Tạo lại" : "Rebuild"}</button>}</div>
          {generated.mode === "ai" && <p className="muted">{language === "vi" ? "Bộ này được AI tạo theo yêu cầu để luyện tập. Kết quả không làm thay đổi mastery và không được dùng làm bằng chứng POWER Evaluate." : "This set was generated by AI for practice. Its result does not change mastery and is not used as POWER Evaluate evidence."}</p>}
          {generated.questions.map((q, index) => {
            const explanation = result?.results.find((r) => r.question_id === q.id);
            return <div className="question-card" key={q.id}>
              <div className="question-meta"><span>#{index + 1}</span><span>{q.question_type}</span><span>{q.difficulty}</span></div>
              <h3>{language === "vi" ? q.stem_vi : q.stem_en}</h3>
              {q.question_type === "mcq" && <div className="option-list">{q.options.map((o) => <label key={o.key} className={answers[q.id] === o.key ? "option selected" : "option"}><input type="radio" name={q.id} checked={answers[q.id] === o.key} onChange={() => setAnswers({ ...answers, [q.id]: o.key })}/><strong>{o.key}.</strong> {language === "vi" ? o.text_vi : o.text_en}</label>)}</div>}
              {q.question_type === "true_false" && <div className="option-list horizontal"><button className={answers[q.id] === true ? "option-button selected" : "option-button"} onClick={() => setAnswers({ ...answers, [q.id]: true })}>{language === "vi" ? "Đúng" : "True"}</button><button className={answers[q.id] === false ? "option-button selected" : "option-button"} onClick={() => setAnswers({ ...answers, [q.id]: false })}>{language === "vi" ? "Sai" : "False"}</button></div>}
              {q.question_type === "short_answer" && <input className="short-answer" value={String(answers[q.id] ?? "")} onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })} placeholder={language === "vi" ? "Nhập câu trả lời" : "Enter answer"}/>} 
              {explanation && <div className={explanation.is_correct ? "feedback correct" : "feedback incorrect"}><strong>{explanation.is_correct ? (language === "vi" ? "Đúng" : "Correct") : (language === "vi" ? "Chưa đúng" : "Not correct")}</strong><p>{language === "vi" ? explanation.explanation_vi : explanation.explanation_en}</p></div>}
            </div>;
          })}
          {!result ? <button className="button primary inline" disabled={busy} onClick={submit}>{busy ? "…" : (language === "vi" ? "Nộp bài" : "Submit")}</button> : <div className="result-banner evaluate-result">
            <strong>{Math.round(result.accuracy * 100)}%</strong>
            <span>{result.correct}/{result.total} {language === "vi" ? "câu đúng" : "correct"}</span>
            {result.power && <div className="evaluate-next-action">
              <p>{language === "vi" ? "POWER đã lưu kết quả này vào pha Evaluate và chuyển chu trình sang Rethink." : "POWER saved this evidence to Evaluate and advanced the cycle to Rethink."}</p>
              <Link className="button primary inline" href={`/learn/${encodeURIComponent(unitCode)}`}>{language === "vi" ? "Tiếp tục Rethink →" : "Continue to Rethink →"}</Link>
            </div>}
          </div>}
        </section>}
      </AppShell>
    </AuthGuard>
  );
}
