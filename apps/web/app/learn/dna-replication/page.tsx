"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { useAuth } from "@/components/auth-provider";
import { useLanguage } from "@/components/language-provider";
import { TutorRenderer } from "@/components/tutor-renderer";
import { apiFetch } from "@/lib/api";
import type { TutorBlock } from "@/lib/types";

const phases = ["PREPARE", "ORGANIZE", "WORK", "EVALUATE", "RETHINK"] as const;
type Phase = (typeof phases)[number];

type DiagnosticItem = {
  code: string;
  concept_code: string;
  question_type: "mcq" | "true_false";
  prompt: string;
  options: { key: string; text: string }[];
};

type PrepareBlueprint = {
  unit_code: string;
  title: string;
  outcomes: string[];
  diagnostic_items: DiagnosticItem[];
};

type GoalFeedback = {
  score: number;
  max_score: number;
  checks: Record<string, boolean>;
  suggestions: string[];
  example: string;
};

type PrepareState = {
  goal?: string;
  target_minutes?: number;
  confidence?: number;
  prior_knowledge?: string;
  diagnostic_answers?: Record<string, string | boolean>;
  goal_feedback?: GoalFeedback;
  diagnostic?: {
    correct: number;
    total: number;
    readiness: number;
    missing: string[];
    weak_concepts: string[];
  };
};

type OrganizeConcept = {
  code: string;
  name: string;
  description: string;
  is_core: boolean;
  mastery_score: number;
};

type OrganizeLink = {
  source: string;
  relation: string;
  target: string;
};

type OrganizeBlueprint = {
  unit_code: string;
  concepts: OrganizeConcept[];
  relation_options: { code: string; label: string }[];
  minimum_anchor_concepts: number;
  minimum_links: number;
  synthesis_prompt: string;
};

type OrganizeState = {
  anchor_concepts?: string[];
  links?: OrganizeLink[];
  synthesis?: string;
  unique_concepts?: string[];
  coverage?: number;
};

type PowerSession = {
  id: string;
  current_phase: Phase;
  status: string;
  unit: { code: string; name_vi: string; name_en: string };
  phases: Partial<Record<Phase, { state: Record<string, unknown>; completed_at: string | null }>>;
  resumed?: boolean;
};

const smartLabelsVi: Record<string, string> = {
  specific: "Cụ thể",
  measurable: "Đo được",
  achievable: "Khả thi",
  relevant: "Liên quan",
  time_bound: "Có thời hạn",
};
const smartLabelsEn: Record<string, string> = {
  specific: "Specific",
  measurable: "Measurable",
  achievable: "Achievable",
  relevant: "Relevant",
  time_bound: "Time-bound",
};

export default function LearnPage() {
  const { language } = useLanguage();
  const { user, devMode, loading: authLoading } = useAuth();
  const [session, setSession] = useState<PowerSession | null>(null);
  const [blueprint, setBlueprint] = useState<PrepareBlueprint | null>(null);
  const [organizeBlueprint, setOrganizeBlueprint] = useState<OrganizeBlueprint | null>(null);
  const [phase, setPhase] = useState<Phase>("PREPARE");
  const [goal, setGoal] = useState("");
  const [targetMinutes, setTargetMinutes] = useState(30);
  const [confidence, setConfidence] = useState(3);
  const [priorKnowledge, setPriorKnowledge] = useState("");
  const [diagnosticAnswers, setDiagnosticAnswers] = useState<Record<string, string | boolean>>({});
  const [goalFeedback, setGoalFeedback] = useState<GoalFeedback | null>(null);
  const [anchorConcepts, setAnchorConcepts] = useState<string[]>([]);
  const [organizeLinks, setOrganizeLinks] = useState<OrganizeLink[]>([
    { source: "", relation: "", target: "" },
    { source: "", relation: "", target: "" },
    { source: "", relation: "", target: "" },
  ]);
  const [organizeSynthesis, setOrganizeSynthesis] = useState("");
  const [reflection, setReflection] = useState("");
  const [message, setMessage] = useState("");
  const [blocks, setBlocks] = useState<TutorBlock[]>([]);
  const [busy, setBusy] = useState(false);
  const [sessionBusy, setSessionBusy] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);
  const [tutorProvider, setTutorProvider] = useState<string | null>(null);
  const [retrievalCount, setRetrievalCount] = useState<number | null>(null);

  useEffect(() => {
    if (authLoading || (!devMode && !user)) return;
    let cancelled = false;
    const load = async () => {
      setSessionBusy(true);
      try {
        const [bp, obp, ps] = await Promise.all([
          apiFetch<PrepareBlueprint>(`/power/prepare/blueprint?unit_code=B12_DNA_REPLICATION&language=${language}`),
          apiFetch<OrganizeBlueprint>(`/power/organize/blueprint?unit_code=B12_DNA_REPLICATION&language=${language}`),
          apiFetch<PowerSession>("/power/sessions", {
            method: "POST",
            body: JSON.stringify({ unit_code: "B12_DNA_REPLICATION", language }),
          }),
        ]);
        if (cancelled) return;
        setBlueprint(bp);
        setOrganizeBlueprint(obp);
        setSession(ps);
        setPhase(ps.current_phase);
        const saved = (ps.phases?.PREPARE?.state || {}) as PrepareState;
        setGoal(saved.goal || "");
        setTargetMinutes(saved.target_minutes || 30);
        setConfidence(saved.confidence || 3);
        setPriorKnowledge(saved.prior_knowledge || "");
        setDiagnosticAnswers(saved.diagnostic_answers || {});
        setGoalFeedback(saved.goal_feedback || null);
        const savedOrganize = (ps.phases?.ORGANIZE?.state || {}) as OrganizeState;
        setAnchorConcepts(savedOrganize.anchor_concepts || []);
        setOrganizeSynthesis(savedOrganize.synthesis || "");
        const savedLinks = savedOrganize.links || [];
        setOrganizeLinks(savedLinks.length >= 3 ? savedLinks : [
          ...savedLinks,
          ...Array.from({ length: 3 - savedLinks.length }, () => ({ source: "", relation: "", target: "" })),
        ]);
      } catch (error) {
        if (!cancelled) setNotice(error instanceof Error ? error.message : "Unable to load POWER session");
      } finally {
        if (!cancelled) setSessionBusy(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [authLoading, devMode, user, language]);

  const diagnosticComplete = useMemo(() => {
    if (!blueprint) return false;
    return blueprint.diagnostic_items.every((item) => diagnosticAnswers[item.code] !== undefined);
  }, [blueprint, diagnosticAnswers]);

  const validOrganizeLinks = useMemo(
    () => organizeLinks.filter((link) => link.source && link.relation && link.target && link.source !== link.target),
    [organizeLinks],
  );

  const organizeCoverage = useMemo(() => {
    const used = new Set(anchorConcepts);
    validOrganizeLinks.forEach((link) => { used.add(link.source); used.add(link.target); });
    const total = organizeBlueprint?.concepts.length || 0;
    return { used: used.size, total, ratio: total ? used.size / total : 0 };
  }, [anchorConcepts, validOrganizeLinks, organizeBlueprint]);

  const organizeCanComplete = Boolean(
    organizeBlueprint
      && anchorConcepts.length >= organizeBlueprint.minimum_anchor_concepts
      && validOrganizeLinks.length >= organizeBlueprint.minimum_links
      && organizeSynthesis.trim().length >= 20,
  );

  const getGoalFeedback = async () => {
    if (!goal.trim()) return;
    const result = await apiFetch<GoalFeedback>("/power/prepare/goal-feedback", {
      method: "POST",
      body: JSON.stringify({
        unit_code: "B12_DNA_REPLICATION",
        language,
        goal,
        target_minutes: targetMinutes,
      }),
    });
    setGoalFeedback(result);
  };

  const savePrepare = async (completed: boolean) => {
    if (!session) return;
    setBusy(true);
    setNotice(null);
    try {
      const result = await apiFetch<{ current_phase: Phase; prepare: PrepareState; session: PowerSession }>(`/power/sessions/${session.id}/prepare`, {
        method: "PUT",
        body: JSON.stringify({
          goal,
          target_minutes: targetMinutes,
          confidence,
          prior_knowledge: priorKnowledge,
          diagnostic_answers: diagnosticAnswers,
          completed,
        }),
      });
      setGoalFeedback(result.prepare.goal_feedback || null);
      setSession(result.session);
      setPhase(result.current_phase);
      setNotice(completed
        ? (language === "vi" ? "Prepare đã hoàn thành. Bây giờ hãy tổ chức kiến thức." : "Prepare is complete. Now organize the knowledge.")
        : (language === "vi" ? "Đã lưu tiến trình Prepare." : "Prepare progress saved."));
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to save Prepare");
    } finally {
      setBusy(false);
    }
  };

  const toggleAnchorConcept = (code: string) => {
    setAnchorConcepts((current) => current.includes(code) ? current.filter((item) => item !== code) : [...current, code]);
  };

  const updateOrganizeLink = (index: number, field: keyof OrganizeLink, value: string) => {
    setOrganizeLinks((current) => current.map((link, i) => i === index ? { ...link, [field]: value } : link));
  };

  const saveOrganize = async (completed: boolean) => {
    if (!session) return;
    setBusy(true);
    setNotice(null);
    try {
      const result = await apiFetch<{ current_phase: Phase; organize: OrganizeState; session: PowerSession }>(`/power/sessions/${session.id}/organize`, {
        method: "PUT",
        body: JSON.stringify({
          anchor_concepts: anchorConcepts,
          links: validOrganizeLinks,
          synthesis: organizeSynthesis,
          completed,
        }),
      });
      setSession(result.session);
      setPhase(result.current_phase);
      setNotice(completed
        ? (language === "vi" ? "Organize đã hoàn thành. Bây giờ hãy làm việc sâu với kiến thức." : "Organize is complete. Now work deeply with the knowledge.")
        : (language === "vi" ? "Đã lưu sơ đồ kiến thức của bạn." : "Your knowledge map has been saved."));
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to save Organize");
    } finally {
      setBusy(false);
    }
  };

  const completeGenericPhase = async (state: Record<string, unknown>) => {
    if (!session) return;
    setBusy(true);
    setNotice(null);
    try {
      const result = await apiFetch<{ current_phase: Phase; cycle_completed: boolean; session: PowerSession }>(`/power/sessions/${session.id}/phase`, {
        method: "PUT",
        body: JSON.stringify({ phase, state, completed: true }),
      });
      setSession(result.session);
      setPhase(result.current_phase);
      setNotice(result.cycle_completed
        ? (language === "vi" ? "Bạn đã hoàn thành một chu trình POWER." : "You completed a POWER cycle.")
        : (language === "vi" ? `Đã hoàn thành ${phase}.` : `${phase} completed.`));
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to update POWER phase");
    } finally {
      setBusy(false);
    }
  };

  const askTutor = async () => {
    if (!message.trim() || !session) return;
    setBusy(true);
    try {
      const res = await apiFetch<{ provider: string; phase: Phase; blocks: TutorBlock[]; retrieval: { count: number } }>("/tutor/respond", {
        method: "POST",
        body: JSON.stringify({
          concept_code: "BIO.DNA.REPLICATION",
          message,
          language,
          power_session_id: session.id,
          phase,
        }),
      });
      setBlocks(res.blocks);
      setTutorProvider(res.provider);
      setRetrievalCount(res.retrieval?.count ?? 0);
    } finally {
      setBusy(false);
    }
  };

  const phaseDone = (p: Phase) => Boolean(session?.phases?.[p]?.completed_at);
  const smartLabels = language === "vi" ? smartLabelsVi : smartLabelsEn;

  const renderPrepare = () => (
    <article className="lesson-card">
      <div className="phase-title-row">
        <div>
          <p className="eyebrow">P · Prepare</p>
          <h2>{language === "vi" ? "Chuẩn bị cho phiên học" : "Prepare for this learning session"}</h2>
        </div>
        <span className="pill">{language === "vi" ? "Người học sở hữu mục tiêu" : "Learner-owned goal"}</span>
      </div>
      <p className="muted">{language === "vi"
        ? "Prepare giúp bạn biết mình sẽ học gì, đã có nền tảng nào và muốn đạt được điều gì trước khi đi sâu vào bài học."
        : "Prepare makes the learning target, prior knowledge, and readiness explicit before you enter the lesson."}</p>

      <div className="prepare-section">
        <h3>1. {language === "vi" ? "Yêu cầu cần đạt" : "Learning outcomes"}</h3>
        <ul className="outcome-list">
          {blueprint?.outcomes.map((outcome) => <li key={outcome}>{outcome}</li>)}
        </ul>
      </div>

      <div className="prepare-section">
        <h3>2. {language === "vi" ? "Mục tiêu của bạn" : "Your goal"}</h3>
        <label className="field-block">
          <span>{language === "vi" ? "Bạn muốn làm được gì sau phiên học này?" : "What do you want to be able to do after this session?"}</span>
          <textarea value={goal} onChange={(e) => setGoal(e.target.value)} placeholder={language === "vi" ? "Ví dụ: Tôi có thể giải thích vì sao mạch chậm cần các đoạn Okazaki và trả lời đúng 4/5 câu liên quan." : "Example: I can explain why the lagging strand needs Okazaki fragments and answer 4/5 related questions correctly."} />
        </label>
        <div className="prepare-inline-grid">
          <label className="field-block compact-field">
            <span>{language === "vi" ? "Thời lượng mục tiêu" : "Target duration"}</span>
            <select value={targetMinutes} onChange={(e) => setTargetMinutes(Number(e.target.value))}>
              {[15, 20, 30, 45, 60, 90].map((m) => <option key={m} value={m}>{m} {language === "vi" ? "phút" : "min"}</option>)}
            </select>
          </label>
          <button className="button secondary smart-button" onClick={getGoalFeedback} disabled={!goal.trim()}>{language === "vi" ? "Kiểm tra mục tiêu SMART" : "Check SMART goal"}</button>
        </div>
        {goalFeedback && <div className="smart-feedback">
          <div className="smart-score"><strong>{goalFeedback.score}/{goalFeedback.max_score}</strong><span>SMART</span></div>
          <div className="smart-checks">
            {Object.entries(goalFeedback.checks).map(([key, ok]) => <span key={key} className={ok ? "smart-chip ok" : "smart-chip"}>{ok ? "✓" : "○"} {smartLabels[key] || key}</span>)}
          </div>
          {goalFeedback.suggestions.length > 0 && <ul>{goalFeedback.suggestions.map((x) => <li key={x}>{x}</li>)}</ul>}
          <p><strong>{language === "vi" ? "Ví dụ tham khảo (không bắt buộc sao chép):" : "Example for reference (do not copy unless it fits you):"}</strong> {goalFeedback.example}</p>
        </div>}
      </div>

      <div className="prepare-section">
        <h3>3. {language === "vi" ? "Kiến thức nền và sự tự tin" : "Prior knowledge and confidence"}</h3>
        <label className="field-block">
          <span>{language === "vi" ? "Bạn đã biết gì về DNA hoặc tái bản DNA?" : "What do you already know about DNA or DNA replication?"}</span>
          <textarea value={priorKnowledge} onChange={(e) => setPriorKnowledge(e.target.value)} placeholder={language === "vi" ? "Viết ngắn gọn bằng lời của bạn. Có thể để trống nếu chưa chắc." : "Write briefly in your own words. You may leave this blank if unsure."} />
        </label>
        <div className="confidence-row">
          <span>{language === "vi" ? "Mức tự tin trước khi học:" : "Confidence before learning:"}</span>
          {[1, 2, 3, 4, 5].map((n) => <button key={n} className={confidence === n ? "confidence-button active" : "confidence-button"} onClick={() => setConfidence(n)}>{n}</button>)}
        </div>
      </div>

      <div className="prepare-section">
        <h3>4. {language === "vi" ? "Kiểm tra nhanh kiến thức tiên quyết" : "Quick prerequisite check"}</h3>
        <p className="muted">{language === "vi" ? "Đây không phải bài kiểm tra lấy điểm. POWER dùng kết quả để biết bạn cần được scaffold ở đâu." : "This is not a graded test. POWER uses it to decide where you may need scaffolding."}</p>
        <div className="diagnostic-list">
          {blueprint?.diagnostic_items.map((item, index) => <div className="diagnostic-item" key={item.code}>
            <strong>{index + 1}. {item.prompt}</strong>
            {item.question_type === "true_false" ? <div className="diagnostic-options">
              {[{ key: "true", value: true, label: language === "vi" ? "Đúng" : "True" }, { key: "false", value: false, label: language === "vi" ? "Sai" : "False" }].map((opt) => <button key={opt.key} className={diagnosticAnswers[item.code] === opt.value ? "option-button selected" : "option-button"} onClick={() => setDiagnosticAnswers((old) => ({ ...old, [item.code]: opt.value }))}>{opt.label}</button>)}
            </div> : <div className="diagnostic-options wrap">
              {item.options.map((opt) => <button key={opt.key} className={diagnosticAnswers[item.code] === opt.key ? "option-button selected" : "option-button"} onClick={() => setDiagnosticAnswers((old) => ({ ...old, [item.code]: opt.key }))}>{opt.key}. {opt.text}</button>)}
            </div>}
          </div>)}
        </div>
      </div>

      <div className="phase-actions">
        <button className="button secondary" onClick={() => savePrepare(false)} disabled={busy || !goal.trim()}>{language === "vi" ? "Lưu Prepare" : "Save Prepare"}</button>
        <button className="button primary" onClick={() => savePrepare(true)} disabled={busy || !goal.trim() || !diagnosticComplete}>{language === "vi" ? "Hoàn thành Prepare →" : "Complete Prepare →"}</button>
      </div>
    </article>
  );

  const renderOrganize = () => (
    <article className="lesson-card organize-card">
      <div className="phase-title-row">
        <div>
          <p className="eyebrow">O · Organize</p>
          <h2>{language === "vi" ? "Tự xây cấu trúc kiến thức của bạn" : "Build your own knowledge structure"}</h2>
        </div>
        <span className="pill">{language === "vi" ? "Learner-built map" : "Learner-built map"}</span>
      </div>
      <p className="muted">{language === "vi"
        ? "POWER không điền sẵn sơ đồ. Bạn chọn các khái niệm neo, nối chúng theo quan hệ mà bạn cho là có ý nghĩa, rồi giải thích một chuỗi bằng lời của chính mình."
        : "POWER does not fill the map for you. Choose anchor concepts, connect them with meaningful relationships, then explain one chain in your own words."}</p>

      <div className="prepare-section">
        <div className="organize-heading-row">
          <h3>1. {language === "vi" ? "Chọn các khái niệm neo" : "Choose anchor concepts"}</h3>
          <span className="muted">{anchorConcepts.length}/{organizeBlueprint?.minimum_anchor_concepts || 3}+</span>
        </div>
        <div className="concept-bank">
          {organizeBlueprint?.concepts.map((concept) => {
            const selected = anchorConcepts.includes(concept.code);
            return <button key={concept.code} type="button" className={selected ? "concept-card selected" : "concept-card"} onClick={() => toggleAnchorConcept(concept.code)}>
              <strong>{concept.name}</strong>
              <span>{concept.description}</span>
              <small>{language === "vi" ? "Mastery hiện tại" : "Current mastery"}: {Math.round(concept.mastery_score * 100)}%</small>
            </button>;
          })}
        </div>
      </div>

      <div className="prepare-section">
        <div className="organize-heading-row">
          <h3>2. {language === "vi" ? "Tạo các mối quan hệ" : "Create relationships"}</h3>
          <span className="muted">{validOrganizeLinks.length}/{organizeBlueprint?.minimum_links || 3}+</span>
        </div>
        <p className="muted">{language === "vi" ? "Không cần cố đoán một sơ đồ duy nhất. Hãy thể hiện cách bạn đang tổ chức bài học." : "There is no single map to guess. Show how you are currently organizing the lesson."}</p>
        <div className="relation-builder">
          {organizeLinks.map((link, index) => <div className="relation-row" key={index}>
            <select value={link.source} onChange={(e) => updateOrganizeLink(index, "source", e.target.value)}>
              <option value="">{language === "vi" ? "Khái niệm A" : "Concept A"}</option>
              {organizeBlueprint?.concepts.map((concept) => <option key={concept.code} value={concept.code}>{concept.name}</option>)}
            </select>
            <select value={link.relation} onChange={(e) => updateOrganizeLink(index, "relation", e.target.value)}>
              <option value="">{language === "vi" ? "Quan hệ" : "Relationship"}</option>
              {organizeBlueprint?.relation_options.map((option) => <option key={option.code} value={option.code}>{option.label}</option>)}
            </select>
            <select value={link.target} onChange={(e) => updateOrganizeLink(index, "target", e.target.value)}>
              <option value="">{language === "vi" ? "Khái niệm B" : "Concept B"}</option>
              {organizeBlueprint?.concepts.map((concept) => <option key={concept.code} value={concept.code}>{concept.name}</option>)}
            </select>
            {organizeLinks.length > 3 && <button type="button" className="relation-remove" onClick={() => setOrganizeLinks((current) => current.filter((_, i) => i !== index))}>×</button>}
          </div>)}
          <button type="button" className="button secondary inline" onClick={() => setOrganizeLinks((current) => [...current, { source: "", relation: "", target: "" }])}>{language === "vi" ? "+ Thêm quan hệ" : "+ Add relationship"}</button>
        </div>
      </div>

      <div className="prepare-section">
        <div className="organize-heading-row">
          <h3>3. {language === "vi" ? "Xem lại bản đồ đang hình thành" : "Review your emerging map"}</h3>
          <span className="pill">{language === "vi" ? `Bao phủ ${organizeCoverage.used}/${organizeCoverage.total} khái niệm` : `Covers ${organizeCoverage.used}/${organizeCoverage.total} concepts`}</span>
        </div>
        {validOrganizeLinks.length === 0 ? <div className="empty-map">{language === "vi" ? "Thêm ít nhất ba mối quan hệ để bản đồ bắt đầu hình thành." : "Add at least three relationships to start forming your map."}</div> : <div className="learner-map-preview">
          {validOrganizeLinks.map((link, index) => {
            const source = organizeBlueprint?.concepts.find((c) => c.code === link.source)?.name || link.source;
            const target = organizeBlueprint?.concepts.find((c) => c.code === link.target)?.name || link.target;
            const relation = organizeBlueprint?.relation_options.find((r) => r.code === link.relation)?.label || link.relation;
            return <div className="map-link" key={`${link.source}-${link.relation}-${link.target}-${index}`}><strong>{source}</strong><span>{relation}</span><strong>{target}</strong></div>;
          })}
        </div>}
      </div>

      <div className="prepare-section">
        <h3>4. {language === "vi" ? "Diễn đạt cấu trúc bằng lời của bạn" : "Express the structure in your own words"}</h3>
        <label className="field-block">
          <span>{organizeBlueprint?.synthesis_prompt || ""}</span>
          <textarea value={organizeSynthesis} onChange={(e) => setOrganizeSynthesis(e.target.value)} placeholder={language === "vi" ? "Ví dụ: Vì hai mạch DNA ngược chiều... nên..." : "Example: Because the DNA strands are antiparallel... therefore..."} />
        </label>
      </div>

      <div className="phase-actions">
        <button className="button secondary" onClick={() => saveOrganize(false)} disabled={busy}>{language === "vi" ? "Lưu Organize" : "Save Organize"}</button>
        <button className="button primary" onClick={() => saveOrganize(true)} disabled={busy || !organizeCanComplete}>{language === "vi" ? "Hoàn thành Organize →" : "Complete Organize →"}</button>
      </div>
    </article>
  );

  const renderWork = () => (
    <article className="lesson-card">
      <p className="eyebrow">W · Work</p>
      <h2>{language === "vi" ? "Vì sao có mạch dẫn đầu và mạch chậm?" : "Why are there leading and lagging strands?"}</h2>
      <p>{language === "vi" ? "Hai mạch DNA ngược chiều nhau. DNA polymerase chỉ kéo dài mạch mới theo chiều 5′→3′. Vì vậy tại một chạc tái bản, một mạch mới có thể được tổng hợp liên tục, trong khi mạch còn lại phải tạo thành các đoạn ngắn rồi nối lại." : "The two DNA templates are antiparallel. DNA polymerase extends new DNA only 5′→3′. At a replication fork, one new strand can therefore be synthesized continuously while the other must be synthesized as short segments that are later joined."}</p>
      <div className="concept-visual"><div>5′ ─────────────── 3′</div><div className="fork-line">↘ {language === "vi" ? "Mạch dẫn đầu" : "Leading strand"}</div><div className="fork-line">↗ {language === "vi" ? "Mạch chậm · Okazaki" : "Lagging strand · Okazaki"}</div><div>3′ ─────────────── 5′</div></div>
      <p className="muted">{language === "vi" ? "Hãy dùng Tutor ở bên phải để hỏi, yêu cầu ví dụ hoặc tự kiểm tra cách hiểu của bạn." : "Use the Tutor on the right to ask, request an example, or check your own explanation."}</p>
      <button className="button primary inline" disabled={busy} onClick={() => completeGenericPhase({ work_completed: true })}>{language === "vi" ? "Tôi đã xử lý nội dung chính →" : "I worked through the core content →"}</button>
    </article>
  );

  const renderEvaluate = () => (
    <article className="lesson-card">
      <p className="eyebrow">E · Evaluate</p>
      <h2>{language === "vi" ? "Thu bằng chứng về mức độ hiểu" : "Collect evidence of understanding"}</h2>
      <p>{language === "vi" ? "Evaluate không chỉ cho điểm. Hãy làm một bộ luyện tập để POWER ghi nhận câu đúng, câu sai và mức độ làm chủ từng khái niệm." : "Evaluate is more than a score. Complete a practice set so POWER can record correct/incorrect responses and concept mastery."}</p>
      <Link className="button primary inline" href="/practice">{language === "vi" ? "Mở Practice" : "Open Practice"}</Link>
      <button className="button secondary inline evaluate-complete" disabled={busy} onClick={() => completeGenericPhase({ practice_reviewed: true })}>{language === "vi" ? "Tôi đã hoàn thành và xem phản hồi →" : "I completed practice and reviewed feedback →"}</button>
    </article>
  );

  const renderRethink = () => (
    <article className="lesson-card">
      <p className="eyebrow">R · Rethink</p>
      <h2>{language === "vi" ? "Nhìn lại để điều chỉnh lần học tiếp theo" : "Reflect and adjust the next learning cycle"}</h2>
      <p>{language === "vi" ? "Không chỉ ghi 'đúng/sai'. Hãy chỉ ra điều bạn đã hiểu rõ hơn, một lỗi hoặc điểm còn mơ hồ, và cách bạn sẽ điều chỉnh." : "Do not stop at right/wrong. State what became clearer, one error or uncertainty, and how you will adjust."}</p>
      <label className="field-block"><span>{language === "vi" ? "Phản tư của bạn" : "Your reflection"}</span><textarea value={reflection} onChange={(e) => setReflection(e.target.value)} placeholder={language === "vi" ? "Tôi từng nghĩ..., sau khi học tôi nhận ra..., lần tới tôi sẽ..." : "I used to think..., now I realize..., next time I will..."} /></label>
      <button className="button primary inline" disabled={busy || reflection.trim().length < 10} onClick={() => completeGenericPhase({ reflection })}>{language === "vi" ? "Hoàn thành chu trình POWER" : "Complete POWER cycle"}</button>
    </article>
  );

  const quickActions = phase === "PREPARE"
    ? [language === "vi" ? "Hỏi tôi một câu kiến thức nền" : "Ask me one prior-knowledge question", language === "vi" ? "Giúp tôi làm rõ mục tiêu" : "Help clarify my goal"]
    : phase === "ORGANIZE"
      ? [language === "vi" ? "Gợi ý quan hệ giữa các khái niệm" : "Suggest concept relationships", language === "vi" ? "Cho tôi một bảng so sánh" : "Give me a comparison table"]
      : phase === "RETHINK"
        ? [language === "vi" ? "Giúp tôi tìm nguyên nhân sai" : "Help identify why I was wrong", language === "vi" ? "Hỏi tôi một câu phản tư" : "Ask me a reflection question"]
        : [language === "vi" ? "Giải thích đơn giản hơn" : "Explain more simply", language === "vi" ? "So sánh hai mạch" : "Compare the two strands", language === "vi" ? "Kiểm tra tôi" : "Quiz me"];

  return (
    <AuthGuard>
      <AppShell>
        <div className="page-heading"><div><p className="eyebrow">Biology 12 · POWER learning cycle</p><h1>{language === "vi" ? "DNA và cơ chế tái bản DNA" : "DNA and DNA replication"}</h1></div>{session?.resumed && <span className="pill">{language === "vi" ? "Đã tiếp tục phiên trước" : "Resumed previous session"}</span>}</div>
        <div className="power-stepper">
          {phases.map((p) => <div key={p} className={["power-step", p === phase ? "active" : "", phaseDone(p) ? "done" : ""].filter(Boolean).join(" ")}>{phaseDone(p) ? "✓" : p[0]}<span>{p}</span></div>)}
        </div>
        {notice && <div className="notice-banner">{notice}</div>}
        {sessionBusy ? <div className="card loading-card">{language === "vi" ? "Đang mở phiên POWER…" : "Opening POWER session…"}</div> : <div className="lesson-layout">
          {phase === "PREPARE" && renderPrepare()}
          {phase === "ORGANIZE" && renderOrganize()}
          {phase === "WORK" && renderWork()}
          {phase === "EVALUATE" && renderEvaluate()}
          {phase === "RETHINK" && renderRethink()}
          <aside className="tutor-card">
            <div className="tutor-header"><div><span className="pill">POWER Tutor · {phase}</span><h3>{language === "vi" ? "Hỗ trợ đúng pha học tập" : "Phase-aware learning support"}</h3></div></div>
            {tutorProvider && <div><span className="pill">{tutorProvider === "openai" ? "OpenAI" : "Mock"}</span> <span className="muted">{language === "vi" ? `Retrieval: ${retrievalCount ?? 0} đoạn` : `Retrieval: ${retrievalCount ?? 0} chunks`}</span></div>}
            {tutorProvider === "mock" && <p className="muted">{language === "vi" ? "Tutor đang chạy mock mode. Hãy dùng AI_PROVIDER=openai để kiểm thử Tutor thật." : "Tutor is running in mock mode. Use AI_PROVIDER=openai to test the real Tutor."}</p>}
            <div className="quick-actions">{quickActions.map((x) => <button key={x} onClick={() => setMessage(x)}>{x}</button>)}</div>
            {blocks.length > 0 && <TutorRenderer blocks={blocks} />}
            <div className="tutor-input"><textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder={language === "vi" ? `Hỏi POWER trong pha ${phase}…` : `Ask POWER during ${phase}…`} /><button className="button primary" disabled={busy || !session} onClick={askTutor}>{busy ? "…" : (language === "vi" ? "Gửi" : "Send")}</button></div>
          </aside>
        </div>}
      </AppShell>
    </AuthGuard>
  );
}
