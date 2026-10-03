"use client";

import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { useLanguage } from "@/components/language-provider";
import { apiFetch } from "@/lib/api";
import type { PracticeQuestion } from "@/lib/types";

type Generated = { practice_set_id: string; mode: string; questions: PracticeQuestion[] };

type Result = { accuracy: number; correct: number; total: number; results: { question_id: string; is_correct: boolean; explanation_vi: string; explanation_en: string }[] };

export default function PracticePage() {
  const { language } = useLanguage();
  const [mode, setMode] = useState<"custom" | "adaptive">("adaptive");
  const [difficulty, setDifficulty] = useState("auto");
  const [count, setCount] = useState(6);
  const [types, setTypes] = useState(["mcq", "true_false", "short_answer"]);
  const [generated, setGenerated] = useState<Generated | null>(null);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [result, setResult] = useState<Result | null>(null);

  const toggleType = (type: string) => setTypes((old) => old.includes(type) ? old.filter((x) => x !== type) : [...old, type]);

  const generate = async () => {
    setResult(null);
    const res = await apiFetch<Generated>("/practice/generate", {
      method: "POST",
      body: JSON.stringify({ mode, unit_code: "B12_DNA_REPLICATION", difficulty, question_types: types, question_count: count }),
    });
    setGenerated(res); setAnswers({});
  };

  const submit = async () => {
    if (!generated) return;
    const payload = generated.questions.map((q) => ({ question_id: q.id, answer: answers[q.id] ?? "", response_time_ms: null, hint_used: false }));
    const res = await apiFetch<Result>(`/practice/${generated.practice_set_id}/submit`, { method: "POST", body: JSON.stringify({ answers: payload }) });
    setResult(res);
  };

  return (
    <AuthGuard>
      <AppShell>
        <div className="page-heading"><div><p className="eyebrow">Practice Engine</p><h1>{language === "vi" ? "Luyện tập" : "Practice"}</h1></div></div>
        {!generated && <section className="practice-builder card">
          <div className="mode-grid">
            <button className={mode === "adaptive" ? "mode-card active" : "mode-card"} onClick={() => setMode("adaptive")}><strong>✨ {language === "vi" ? "Phù hợp với tôi" : "Recommended for me"}</strong><span>{language === "vi" ? "Ưu tiên khái niệm còn yếu dựa trên mastery hiện tại." : "Prioritize weak concepts from current mastery."}</span></button>
            <button className={mode === "custom" ? "mode-card active" : "mode-card"} onClick={() => setMode("custom")}><strong>{language === "vi" ? "Tự chọn" : "Custom"}</strong><span>{language === "vi" ? "Chọn mức độ và dạng câu hỏi." : "Choose difficulty and question formats."}</span></button>
          </div>
          <div className="form-grid">
            <label>{language === "vi" ? "Nội dung" : "Topic"}<select disabled><option>{language === "vi" ? "Tái bản DNA" : "DNA replication"}</option></select></label>
            <label>{language === "vi" ? "Mức độ khó" : "Difficulty"}<select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}><option value="auto">Adaptive / Auto</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
            <label>{language === "vi" ? "Số câu" : "Questions"}<select value={count} onChange={(e) => setCount(Number(e.target.value))}><option>3</option><option>6</option><option>9</option><option>12</option></select></label>
          </div>
          <div className="check-row">
            {[['mcq', language === 'vi' ? 'Trắc nghiệm' : 'Multiple choice'], ['true_false', language === 'vi' ? 'Đúng/Sai' : 'True/False'], ['short_answer', language === 'vi' ? 'Trả lời ngắn' : 'Short answer']].map(([value,label]) => <label key={value}><input type="checkbox" checked={types.includes(value)} onChange={() => toggleType(value)} /> {label}</label>)}
          </div>
          <button className="button primary inline" disabled={types.length === 0} onClick={generate}>{language === "vi" ? "Tạo bộ luyện tập" : "Generate practice"}</button>
        </section>}
        {generated && <section className="question-list">
          <div className="section-toolbar"><strong>{generated.questions.length} {language === "vi" ? "câu hỏi" : "questions"}</strong><button className="text-button" onClick={() => setGenerated(null)}>{language === "vi" ? "Tạo lại" : "Rebuild"}</button></div>
          {generated.questions.map((q, index) => {
            const explanation = result?.results.find((r) => r.question_id === q.id);
            return <div className="question-card" key={q.id}>
              <div className="question-meta"><span>#{index + 1}</span><span>{q.question_type}</span><span>{q.difficulty}</span></div>
              <h3>{language === "vi" ? q.stem_vi : q.stem_en}</h3>
              {q.question_type === "mcq" && <div className="option-list">{q.options.map((o) => <label key={o.key} className={answers[q.id] === o.key ? "option selected" : "option"}><input type="radio" name={q.id} checked={answers[q.id] === o.key} onChange={() => setAnswers({...answers,[q.id]:o.key})}/><strong>{o.key}.</strong> {language === "vi" ? o.text_vi : o.text_en}</label>)}</div>}
              {q.question_type === "true_false" && <div className="option-list horizontal"><button className={answers[q.id] === true ? "option-button selected" : "option-button"} onClick={() => setAnswers({...answers,[q.id]:true})}>{language === "vi" ? "Đúng" : "True"}</button><button className={answers[q.id] === false ? "option-button selected" : "option-button"} onClick={() => setAnswers({...answers,[q.id]:false})}>{language === "vi" ? "Sai" : "False"}</button></div>}
              {q.question_type === "short_answer" && <input className="short-answer" value={answers[q.id] ?? ""} onChange={(e) => setAnswers({...answers,[q.id]:e.target.value})} placeholder={language === "vi" ? "Nhập câu trả lời" : "Enter answer"}/>}
              {explanation && <div className={explanation.is_correct ? "feedback correct" : "feedback incorrect"}><strong>{explanation.is_correct ? (language === "vi" ? "Đúng" : "Correct") : (language === "vi" ? "Chưa đúng" : "Not correct")}</strong><p>{language === "vi" ? explanation.explanation_vi : explanation.explanation_en}</p></div>}
            </div>;
          })}
          {!result ? <button className="button primary inline" onClick={submit}>{language === "vi" ? "Nộp bài" : "Submit"}</button> : <div className="result-banner"><strong>{Math.round(result.accuracy * 100)}%</strong><span>{result.correct}/{result.total} {language === "vi" ? "câu đúng" : "correct"}</span></div>}
        </section>}
      </AppShell>
    </AuthGuard>
  );
}
