"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { useAuth } from "@/components/auth-provider";
import { useLanguage } from "@/components/language-provider";
import { PowerTutorRenderer, type PowerTutorBlock } from "@/components/power-tutor-renderer";
import { apiFetch } from "@/lib/api";

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

type WorkTask = {
  code: string;
  title: string;
  prompt: string;
  concept_codes: string[];
  minimum_chars: number;
  scaffold: string[];
};

type WorkBlueprint = {
  unit_code: string;
  title: string;
  intro: string;
  tasks: WorkTask[];
  self_check_prompt: string;
};

type WorkState = {
  responses?: Record<string, string>;
  completed_tasks?: string[];
  confidence_after?: number;
  evidence_chars?: number;
  completion_ratio?: number;
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

type EvaluateState = {
  practice_set_id?: string;
  practice_attempt_id?: string;
  accuracy?: number;
  correct?: number;
  total?: number;
  concepts?: EvaluateConcept[];
  weak_concepts?: string[];
  evidence_ready?: boolean;
};


type CandidateMisconception = {
  code: string;
  concept_code: string;
  concept_name_vi: string;
  concept_name_en: string;
  statement_vi: string;
  statement_en: string;
  correction_vi: string;
  correction_en: string;
  confidence: number;
  evidence_count: number;
  question_codes: string[];
};

type RethinkRecommendation = {
  type: string;
  priority: number;
  title: string;
  reason: string;
  route: string;
  weak_concepts: string[];
  confirmed_misconceptions: string[];
};

type RethinkState = {
  understanding_gain?: string;
  error_cause?: string;
  corrected_explanation?: string;
  action_plan?: string;
  confidence_after_rethink?: number;
  confirmed_misconceptions?: string[];
  recommendation?: RethinkRecommendation;
};

type RethinkBlueprint = {
  ready: boolean;
  current_phase: Phase;
  cycle_status: string;
  evaluate: EvaluateState;
  confidence_before?: number | null;
  confidence_after_work?: number | null;
  candidate_misconceptions: CandidateMisconception[];
  saved: RethinkState;
  completed_at?: string | null;
  recommendation_preview: RethinkRecommendation;
};

type UnitDetail = {
  code: string;
  name_vi: string;
  name_en: string;
  grade: number;
  grade_name_vi: string;
  grade_name_en: string;
  unit_type: string;
  lesson_number: number | null;
  printed_page_start: number | null;
  printed_page_end: number | null;
  is_power_ready: boolean;
  primary_concept_code: string | null;
  parent_code: string | null;
  parent_name_vi: string | null;
  parent_name_en: string | null;
  sources: { code: string; title: string; source_role: string; printed_page_start: number | null; printed_page_end: number | null; pdf_page_start: number | null; pdf_page_end: number | null }[];
};

type PowerSession = {
  id: string;
  current_phase: Phase;
  status: string;
  created_at?: string;
  updated_at?: string;
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
  const params = useParams<{ unitCode: string }>();
  const unitCode = decodeURIComponent(params.unitCode || "B12_DNA_REPLICATION");
  const { language } = useLanguage();
  const { user, devMode, loading: authLoading } = useAuth();
  const [unitDetail, setUnitDetail] = useState<UnitDetail | null>(null);
  const [session, setSession] = useState<PowerSession | null>(null);
  const [blueprint, setBlueprint] = useState<PrepareBlueprint | null>(null);
  const [organizeBlueprint, setOrganizeBlueprint] = useState<OrganizeBlueprint | null>(null);
  const [workBlueprint, setWorkBlueprint] = useState<WorkBlueprint | null>(null);
  const [rethinkBlueprint, setRethinkBlueprint] = useState<RethinkBlueprint | null>(null);
  const [phase, setPhase] = useState<Phase>("PREPARE");
  const [viewPhase, setViewPhase] = useState<Phase>("PREPARE");
  const [sessionHistory, setSessionHistory] = useState<PowerSession[]>([]);
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
  const [workResponses, setWorkResponses] = useState<Record<string, string>>({});
  const [workConfidence, setWorkConfidence] = useState(3);
  const [understandingGain, setUnderstandingGain] = useState("");
  const [errorCause, setErrorCause] = useState("");
  const [correctedExplanation, setCorrectedExplanation] = useState("");
  const [actionPlan, setActionPlan] = useState("");
  const [rethinkConfidence, setRethinkConfidence] = useState(3);
  const [confirmedMisconceptions, setConfirmedMisconceptions] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [blocks, setBlocks] = useState<PowerTutorBlock[]>([]);
  const [busy, setBusy] = useState(false);
  const [sessionBusy, setSessionBusy] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);
  const [tutorProvider, setTutorProvider] = useState<string | null>(null);
  const [retrievalCount, setRetrievalCount] = useState<number | null>(null);

  const hydratePowerSession = (ps: PowerSession) => {
    setSession(ps);
    setPhase(ps.current_phase);
    setViewPhase(ps.current_phase);
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
    const savedWork = (ps.phases?.WORK?.state || {}) as WorkState;
    setWorkResponses(savedWork.responses || {});
    setWorkConfidence(savedWork.confidence_after || 3);
    const rethinkState = (ps.phases?.RETHINK?.state || {}) as RethinkState;
    setUnderstandingGain(rethinkState.understanding_gain || "");
    setErrorCause(rethinkState.error_cause || "");
    setCorrectedExplanation(rethinkState.corrected_explanation || "");
    setActionPlan(rethinkState.action_plan || "");
    setRethinkConfidence(rethinkState.confidence_after_rethink || 3);
    setConfirmedMisconceptions(rethinkState.confirmed_misconceptions || []);
    setBlocks([]);
    setTutorProvider(null);
    setRetrievalCount(null);
  };

  const loadRethinkBlueprint = async (sessionId: string) => {
    try {
      const result = await apiFetch<RethinkBlueprint>(`/power/sessions/${sessionId}/rethink/blueprint?language=${language}`);
      setRethinkBlueprint(result);
      return result;
    } catch (error) {
      setRethinkBlueprint(null);
      throw error;
    }
  };

  useEffect(() => {
    if (authLoading || (!devMode && !user)) return;
    let cancelled = false;
    const load = async () => {
      setSessionBusy(true);
      try {
        const [detail, bp, obp, wbp, ps] = await Promise.all([
          apiFetch<UnitDetail>(`/catalog/${encodeURIComponent(unitCode)}`),
          apiFetch<PrepareBlueprint>(`/power/prepare/blueprint?unit_code=${encodeURIComponent(unitCode)}&language=${language}`),
          apiFetch<OrganizeBlueprint>(`/power/organize/blueprint?unit_code=${encodeURIComponent(unitCode)}&language=${language}`),
          apiFetch<WorkBlueprint>(`/power/work/blueprint?unit_code=${encodeURIComponent(unitCode)}&language=${language}`),
          apiFetch<PowerSession>("/power/sessions", {
            method: "POST",
            body: JSON.stringify({ unit_code: unitCode, language }),
          }),
        ]);
        if (cancelled) return;
        setUnitDetail(detail);
        setBlueprint(bp);
        setOrganizeBlueprint(obp);
        setWorkBlueprint(wbp);
        hydratePowerSession(ps);
        await loadRethinkBlueprint(ps.id);
        const history = await apiFetch<{ sessions: PowerSession[] }>(`/power/sessions/history?unit_code=${encodeURIComponent(unitCode)}&limit=10`);
        if (!cancelled) setSessionHistory(history.sessions);
      } catch (error) {
        if (!cancelled) setNotice(error instanceof Error ? error.message : "Unable to load POWER session");
      } finally {
        if (!cancelled) setSessionBusy(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [authLoading, devMode, user, language, unitCode]);

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

  const workTaskStatus = useMemo(() => {
    if (!workBlueprint) return { complete: 0, total: 0, canComplete: false };
    const complete = workBlueprint.tasks.filter((task) => (workResponses[task.code] || "").trim().length >= task.minimum_chars).length;
    return { complete, total: workBlueprint.tasks.length, canComplete: complete === workBlueprint.tasks.length };
  }, [workBlueprint, workResponses]);

  const getGoalFeedback = async () => {
    if (!goal.trim()) return;
    const result = await apiFetch<GoalFeedback>("/power/prepare/goal-feedback", {
      method: "POST",
      body: JSON.stringify({
        unit_code: unitCode,
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
      if (completed && phase === "PREPARE") setViewPhase(result.current_phase);
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
      if (completed && phase === "ORGANIZE") setViewPhase(result.current_phase);
      setNotice(completed
        ? (language === "vi" ? "Organize đã hoàn thành. Bây giờ hãy làm việc sâu với kiến thức." : "Organize is complete. Now work deeply with the knowledge.")
        : (language === "vi" ? "Đã lưu sơ đồ kiến thức của bạn." : "Your knowledge map has been saved."));
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to save Organize");
    } finally {
      setBusy(false);
    }
  };

  const saveWork = async (completed: boolean) => {
    if (!session) return;
    setBusy(true);
    setNotice(null);
    try {
      const result = await apiFetch<{ current_phase: Phase; work: WorkState; session: PowerSession }>(`/power/sessions/${session.id}/work`, {
        method: "PUT",
        body: JSON.stringify({
          responses: workResponses,
          confidence_after: workConfidence,
          completed,
        }),
      });
      setSession(result.session);
      setPhase(result.current_phase);
      if (completed && phase === "WORK") setViewPhase(result.current_phase);
      setNotice(completed
        ? (language === "vi" ? "Work đã hoàn thành. Bây giờ hãy thu bằng chứng đánh giá." : "Work is complete. Now collect evaluation evidence.")
        : (language === "vi" ? "Đã lưu bằng chứng Work của bạn." : "Your Work evidence has been saved."));
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to save Work");
    } finally {
      setBusy(false);
    }
  };

  const saveRethink = async (completed: boolean) => {
    if (!session) return;
    setBusy(true);
    setNotice(null);
    try {
      const result = await apiFetch<{ current_phase: Phase; cycle_completed: boolean; rethink: RethinkState; recommendation: RethinkRecommendation; session: PowerSession }>(`/power/sessions/${session.id}/rethink`, {
        method: "PUT",
        body: JSON.stringify({
          understanding_gain: understandingGain,
          error_cause: errorCause,
          corrected_explanation: correctedExplanation,
          action_plan: actionPlan,
          confidence_after_rethink: rethinkConfidence,
          confirmed_misconceptions: confirmedMisconceptions,
          completed,
        }),
      });
      setSession(result.session);
      setPhase(result.current_phase);
      await loadRethinkBlueprint(session.id);
      setNotice(result.cycle_completed
        ? (language === "vi" ? "Bạn đã hoàn thành chu trình POWER. Rethink, hiểu lầm đã xác nhận và gợi ý tiếp theo đã được lưu vào learner model." : "You completed the POWER cycle. Rethink evidence, confirmed misconceptions, and the next recommendation were saved to the learner model.")
        : (language === "vi" ? "Đã lưu Rethink." : "Rethink saved."));
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to save Rethink");
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
        body: JSON.stringify({ phase: viewPhase, state, completed: true }),
      });
      setSession(result.session);
      setPhase(result.current_phase);
      setViewPhase(result.current_phase);
      setNotice(result.cycle_completed
        ? (language === "vi" ? "Bạn đã hoàn thành một chu trình POWER. Bạn vẫn có thể mở lại từng pha để xem và chỉnh sửa." : "You completed a POWER cycle. You can still reopen each phase to review or edit it.")
        : (language === "vi" ? `Đã hoàn thành ${viewPhase}.` : `${viewPhase} completed.`));
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
      const res = await apiFetch<{ provider: string; phase: Phase; blocks: PowerTutorBlock[]; retrieval: { count: number } }>("/tutor/respond", {
        method: "POST",
        body: JSON.stringify({
          concept_code: unitDetail?.primary_concept_code || undefined,
          message,
          language,
          power_session_id: session.id,
          phase: viewPhase,
        }),
      });
      setBlocks(res.blocks);
      setTutorProvider(res.provider);
      setRetrievalCount(res.retrieval?.count ?? 0);
    } finally {
      setBusy(false);
    }
  };

  const openPhase = (target: Phase) => {
    if (!session?.phases?.[target] && target !== phase) return;
    setViewPhase(target);
    setBlocks([]);
    setTutorProvider(null);
    setRetrievalCount(null);
    setNotice(target === phase
      ? null
      : (language === "vi" ? `Bạn đang xem lại pha ${target}. Tiến trình hiện tại vẫn ở ${phase}.` : `You are reviewing ${target}. Your current progression remains at ${phase}.`));
  };

  const startNewCycle = async () => {
    if (!session || session.status !== "completed") return;
    setBusy(true);
    setNotice(null);
    try {
      const ps = await apiFetch<PowerSession>("/power/sessions", {
        method: "POST",
        body: JSON.stringify({ unit_code: unitCode, language, force_new: true }),
      });
      hydratePowerSession(ps);
      await loadRethinkBlueprint(ps.id);
      const history = await apiFetch<{ sessions: PowerSession[] }>(`/power/sessions/history?unit_code=${encodeURIComponent(unitCode)}&limit=10`);
      setSessionHistory(history.sessions);
      setNotice(language === "vi" ? "Đã bắt đầu một chu trình POWER mới từ Prepare." : "Started a new POWER cycle from Prepare.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to start a new POWER cycle");
    } finally {
      setBusy(false);
    }
  };

  const switchSession = async (sessionId: string) => {
    if (!sessionId || sessionId === session?.id) return;
    setSessionBusy(true);
    try {
      const ps = await apiFetch<PowerSession>(`/power/sessions/${sessionId}`);
      hydratePowerSession(ps);
      await loadRethinkBlueprint(ps.id);
      setNotice(ps.status === "completed"
        ? (language === "vi" ? "Đang xem một chu trình POWER đã hoàn thành." : "Viewing a completed POWER cycle.")
        : null);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to open POWER cycle");
    } finally {
      setSessionBusy(false);
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
          <textarea value={goal} onChange={(e) => setGoal(e.target.value)} placeholder={language === "vi" ? "Ví dụ: Tôi có thể giải thích một cơ chế cốt lõi của bài và trả lời đúng 4/5 câu liên quan." : "Example: I can explain one core mechanism in this lesson and answer 4/5 related questions correctly."} />
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
          <span>{language === "vi" ? "Bạn đã biết gì về nội dung này?" : "What do you already know about this topic?"}</span>
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
        <button className="button secondary" onClick={() => savePrepare(false)} disabled={busy || !goal.trim()}>{phaseDone("PREPARE") ? (language === "vi" ? "Lưu thay đổi Prepare" : "Save Prepare changes") : (language === "vi" ? "Lưu Prepare" : "Save Prepare")}</button>
        {!phaseDone("PREPARE") && phase === "PREPARE" && <button className="button primary" onClick={() => savePrepare(true)} disabled={busy || !goal.trim() || !diagnosticComplete}>{language === "vi" ? "Hoàn thành Prepare →" : "Complete Prepare →"}</button>}
        {viewPhase !== phase && <button className="button primary" onClick={() => setViewPhase(phase)}>{language === "vi" ? `Trở lại ${phase}` : `Back to ${phase}`}</button>}
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
          <textarea value={organizeSynthesis} onChange={(e) => setOrganizeSynthesis(e.target.value)} placeholder={language === "vi" ? "Hãy mô tả một chuỗi quan hệ quan trọng trong bài..." : "Describe one important relationship chain in this lesson..."} />
        </label>
      </div>

      <div className="phase-actions">
        <button className="button secondary" onClick={() => saveOrganize(false)} disabled={busy}>{phaseDone("ORGANIZE") ? (language === "vi" ? "Lưu thay đổi Organize" : "Save Organize changes") : (language === "vi" ? "Lưu Organize" : "Save Organize")}</button>
        {!phaseDone("ORGANIZE") && phase === "ORGANIZE" && <button className="button primary" onClick={() => saveOrganize(true)} disabled={busy || !organizeCanComplete}>{language === "vi" ? "Hoàn thành Organize →" : "Complete Organize →"}</button>}
        {viewPhase !== phase && <button className="button primary" onClick={() => setViewPhase(phase)}>{language === "vi" ? `Trở lại ${phase}` : `Back to ${phase}`}</button>}
      </div>
    </article>
  );

  const renderWork = () => (
    <article className="lesson-card work-phase-card">
      <div className="phase-title-row">
        <div>
          <p className="eyebrow">W · Work</p>
          <h2>{workBlueprint?.title || (language === "vi" ? "Làm việc sâu với kiến thức" : "Work deeply with the knowledge")}</h2>
        </div>
        <span className="pill">{language === "vi" ? `${workTaskStatus.complete}/${workTaskStatus.total} bằng chứng` : `${workTaskStatus.complete}/${workTaskStatus.total} evidence tasks`}</span>
      </div>
      <p className="muted">{workBlueprint?.intro}</p>

      <div className="work-progress" aria-label={language === "vi" ? "Tiến độ Work" : "Work progress"}>
        <div style={{ width: `${workTaskStatus.total ? (workTaskStatus.complete / workTaskStatus.total) * 100 : 0}%` }} />
      </div>

      <div className="work-task-list">
        {workBlueprint?.tasks.map((task, index) => {
          const value = workResponses[task.code] || "";
          const complete = value.trim().length >= task.minimum_chars;
          return <section className={["work-task", complete ? "complete" : ""].filter(Boolean).join(" ")} key={task.code}>
            <div className="work-task-head">
              <div><span className="task-number">{index + 1}</span><h3>{task.title}</h3></div>
              <span className={complete ? "evidence-ok" : "evidence-pending"}>{complete ? (language === "vi" ? "Đủ evidence" : "Evidence ready") : `${value.trim().length}/${task.minimum_chars}`}</span>
            </div>
            <p className="work-prompt">{task.prompt}</p>
            <details className="work-scaffold">
              <summary>{language === "vi" ? "Gợi ý suy nghĩ" : "Thinking prompts"}</summary>
              <ul>{task.scaffold.map((item) => <li key={item}>{item}</li>)}</ul>
            </details>
            <label className="field-block work-response">
              <span>{language === "vi" ? "Giải thích bằng lời của bạn" : "Explain in your own words"}</span>
              <textarea
                value={value}
                onChange={(e) => setWorkResponses((current) => ({ ...current, [task.code]: e.target.value }))}
                placeholder={language === "vi" ? "Viết lập luận của bạn ở đây. Không cần giống nguyên văn SGK." : "Write your reasoning here. It does not need to copy the textbook wording."}
              />
            </label>
            <button
              type="button"
              className="button secondary tutor-task-button"
              onClick={() => setMessage(language === "vi"
                ? `Tôi đang làm ${task.title}. Nhiệm vụ: ${task.prompt}\n\nCâu trả lời hiện tại của tôi: ${value || "(chưa viết)"}\n\nHãy phản hồi bằng gợi ý và câu hỏi dẫn dắt, đừng viết đáp án hoàn chỉnh thay tôi.`
                : `I am working on ${task.title}. Task: ${task.prompt}\n\nMy current response: ${value || "(not written yet)"}\n\nGive me hints and guiding questions; do not write the full answer for me.`)}
            >{language === "vi" ? "Nhờ POWER Tutor phản hồi" : "Ask POWER Tutor for feedback"}</button>
          </section>;
        })}
      </div>

      <div className="prepare-section work-self-check">
        <h3>{language === "vi" ? "Tự kiểm tra sau khi xử lý nhiệm vụ" : "Self-check after working through the tasks"}</h3>
        <p className="muted">{workBlueprint?.self_check_prompt}</p>
        <div className="confidence-scale">
          {[1, 2, 3, 4, 5].map((value) => <button key={value} type="button" className={workConfidence === value ? "active" : ""} onClick={() => setWorkConfidence(value)}>{value}</button>)}
        </div>
      </div>

      <div className="phase-actions">
        <button className="button secondary" onClick={() => saveWork(false)} disabled={busy}>{phaseDone("WORK") ? (language === "vi" ? "Lưu thay đổi Work" : "Save Work changes") : (language === "vi" ? "Lưu Work" : "Save Work")}</button>
        {!phaseDone("WORK") && phase === "WORK" && <button className="button primary" onClick={() => saveWork(true)} disabled={busy || !workTaskStatus.canComplete}>{language === "vi" ? "Hoàn thành Work →" : "Complete Work →"}</button>}
        {viewPhase !== phase && <button className="button primary" onClick={() => setViewPhase(phase)}>{language === "vi" ? `Trở lại ${phase}` : `Back to ${phase}`}</button>}
      </div>
    </article>
  );

  const renderEvaluate = () => {
    const evaluate = (session?.phases?.EVALUATE?.state || {}) as EvaluateState;
    const hasEvidence = Boolean(session?.phases?.EVALUATE?.completed_at && evaluate.evidence_ready);
    const accuracyPercent = Math.round((evaluate.accuracy || 0) * 100);

    return (
      <article className="lesson-card evaluate-phase-card">
        <p className="eyebrow">E · Evaluate</p>
        <h2>{language === "vi" ? "Thu bằng chứng thật về mức độ hiểu" : "Collect real evidence of understanding"}</h2>
        {!hasEvidence ? <>
          <p>{language === "vi" ? "Evaluate không được hoàn thành bằng một nút xác nhận thủ công. POWER sẽ tạo bộ đánh giá, lưu từng câu trả lời vào database, cập nhật mastery theo khái niệm và tự chuyển sang Rethink sau khi bạn nộp bài." : "Evaluate cannot be completed with a manual confirmation. POWER will create an evaluation set, store each response in the database, update concept mastery, and automatically move to Rethink after submission."}</p>
          {phase === "EVALUATE" ? <Link className="button primary inline" href={session ? `/practice?purpose=evaluate&powerSessionId=${session.id}&unitCode=${encodeURIComponent(unitCode)}` : "/practice"}>{language === "vi" ? "Bắt đầu Evaluate →" : "Start Evaluate →"}</Link> : <div className="review-banner">{language === "vi" ? "Bạn đang xem lại Evaluate nhưng chu trình hiện không ở pha Evaluate." : "You are reviewing Evaluate, but the cycle is not currently in Evaluate."}</div>}
        </> : <>
          <div className="evaluate-summary-grid">
            <div className="evaluate-score-card"><span>{language === "vi" ? "Kết quả" : "Result"}</span><strong>{accuracyPercent}%</strong><small>{evaluate.correct ?? 0}/{evaluate.total ?? 0} {language === "vi" ? "câu đúng" : "correct"}</small></div>
            <div className="evaluate-score-card"><span>{language === "vi" ? "Khái niệm cần xem lại" : "Concepts to revisit"}</span><strong>{evaluate.weak_concepts?.length ?? 0}</strong><small>{language === "vi" ? "dựa trên evidence + mastery" : "from evidence + mastery"}</small></div>
          </div>
          {(evaluate.concepts?.length || 0) > 0 && <div className="evaluate-concept-list">
            <h3>{language === "vi" ? "Kết quả theo khái niệm" : "Concept-level evidence"}</h3>
            {evaluate.concepts?.map((concept) => <div className="evaluate-concept-row" key={concept.concept_code}>
              <div><strong>{language === "vi" ? concept.name_vi : concept.name_en}</strong><span>{concept.concept_code}</span></div>
              <div><b>{Math.round(concept.accuracy * 100)}%</b><span>{concept.correct}/{concept.total}</span></div>
            </div>)}
          </div>}
          <p className="muted">{language === "vi" ? "Kết quả này được lấy trực tiếp từ practice_attempts, question_attempts và concept_mastery trong database; không phải người học tự đánh dấu đã hoàn thành." : "This evidence comes directly from practice_attempts, question_attempts, and concept_mastery in the database; it is not a self-reported completion flag."}</p>
          {viewPhase !== phase && <button className="button primary inline" onClick={() => setViewPhase(phase)}>{language === "vi" ? `Trở lại ${phase}` : `Back to ${phase}`}</button>}
        </>}
      </article>
    );
  };

  const renderRethink = () => {
    const evaluate = rethinkBlueprint?.evaluate || ((session?.phases?.EVALUATE?.state || {}) as EvaluateState);
    const recommendation = ((session?.phases?.RETHINK?.state || {}) as RethinkState).recommendation || rethinkBlueprint?.recommendation_preview;
    const accuracyPercent = Math.round((evaluate.accuracy || 0) * 100);
    const rethinkCanComplete = Boolean(
      rethinkBlueprint?.ready
      && understandingGain.trim().length >= 20
      && errorCause
      && correctedExplanation.trim().length >= 40
      && actionPlan.trim().length >= 20,
    );
    const errorCauseOptions = language === "vi"
      ? [
          ["knowledge_gap", "Thiếu kiến thức nền hoặc chưa nhớ chắc"],
          ["misconception", "Tôi đã hiểu sai một khái niệm"],
          ["careless", "Sơ suất khi đọc hoặc trả lời"],
          ["strategy", "Cách học/cách xử lý câu hỏi chưa phù hợp"],
          ["uncertain", "Tôi chưa xác định rõ nguyên nhân"],
        ]
      : [
          ["knowledge_gap", "Missing or unstable prior knowledge"],
          ["misconception", "I held an incorrect concept"],
          ["careless", "Careless reading or response"],
          ["strategy", "My learning/answering strategy was not effective"],
          ["uncertain", "I am not yet sure of the cause"],
        ];

    return <article className="lesson-card rethink-phase-card">
      <div className="phase-title-row">
        <div>
          <p className="eyebrow">R · Rethink</p>
          <h2>{language === "vi" ? "Biến kết quả đánh giá thành điều chỉnh học tập" : "Turn evaluation evidence into learning adjustments"}</h2>
        </div>
        <span className="pill">{phaseDone("RETHINK") ? (language === "vi" ? "Đã hoàn thành" : "Completed") : (language === "vi" ? "Evidence → Reflection → Action" : "Evidence → Reflection → Action")}</span>
      </div>

      {!rethinkBlueprint?.ready ? <div className="review-banner">
        {language === "vi" ? "Rethink cần dữ liệu Evaluate thật. Hãy hoàn thành bộ đánh giá trước khi kết thúc chu trình." : "Rethink requires real Evaluate evidence. Complete the evaluation before closing the cycle."}
      </div> : <>
        <section className="rethink-section">
          <h3>1. {language === "vi" ? "Nhìn lại bằng chứng" : "Review the evidence"}</h3>
          <div className="evaluate-summary-grid">
            <div className="evaluate-score-card"><span>{language === "vi" ? "Evaluate" : "Evaluate"}</span><strong>{accuracyPercent}%</strong><small>{evaluate.correct ?? 0}/{evaluate.total ?? 0} {language === "vi" ? "câu đúng" : "correct"}</small></div>
            <div className="evaluate-score-card"><span>{language === "vi" ? "Tự tin" : "Confidence"}</span><strong>{rethinkBlueprint.confidence_before ?? "–"} → {rethinkBlueprint.confidence_after_work ?? "–"}</strong><small>{language === "vi" ? "trước học → sau Work" : "before learning → after Work"}</small></div>
          </div>
          {(evaluate.concepts?.length || 0) > 0 && <div className="rethink-evidence-list">
            {evaluate.concepts?.map((concept) => <div className="rethink-evidence-row" key={concept.concept_code}>
              <div><strong>{language === "vi" ? concept.name_vi : concept.name_en}</strong><span>{concept.concept_code}</span></div>
              <b>{Math.round(concept.accuracy * 100)}%</b>
            </div>)}
          </div>}
        </section>

        <section className="rethink-section">
          <h3>2. {language === "vi" ? "Kiểm tra hiểu lầm có thể có" : "Check possible misconceptions"}</h3>
          <p className="muted">{language === "vi" ? "POWER chỉ xem đây là tín hiệu từ các câu sai, không tự kết luận bạn có hiểu lầm. Chỉ đánh dấu nếu mô tả thật sự giống cách bạn đã nghĩ." : "POWER treats these only as signals from wrong answers, not as a diagnosis. Confirm one only if it truly matches how you were thinking."}</p>
          {(rethinkBlueprint.candidate_misconceptions?.length || 0) === 0 ? <div className="rethink-empty">{language === "vi" ? "Chưa có mẫu hiểu lầm cụ thể đủ rõ từ bộ Evaluate này." : "No specific misconception pattern is clear enough from this Evaluate set."}</div> : <div className="misconception-list">
            {rethinkBlueprint.candidate_misconceptions.map((item) => {
              const checked = confirmedMisconceptions.includes(item.code);
              return <label className={checked ? "misconception-card confirmed" : "misconception-card"} key={item.code}>
                <input type="checkbox" checked={checked} onChange={() => setConfirmedMisconceptions((current) => checked ? current.filter((code) => code !== item.code) : [...current, item.code])} />
                <div>
                  <div className="misconception-head"><strong>{language === "vi" ? item.concept_name_vi : item.concept_name_en}</strong><span>{Math.round(item.confidence * 100)}% {language === "vi" ? "tín hiệu" : "signal"}</span></div>
                  <p><b>{language === "vi" ? "Có thể đã nghĩ:" : "Possible prior idea:"}</b> {language === "vi" ? item.statement_vi : item.statement_en}</p>
                  <p><b>{language === "vi" ? "Ý cần đối chiếu:" : "Correction to check:"}</b> {language === "vi" ? item.correction_vi : item.correction_en}</p>
                </div>
              </label>;
            })}
          </div>}
        </section>

        <section className="rethink-section">
          <h3>3. {language === "vi" ? "Phản tư bằng lời của bạn" : "Reflect in your own words"}</h3>
          <label className="field-block"><span>{language === "vi" ? "Điều gì đã trở nên rõ hơn?" : "What became clearer?"}</span><textarea value={understandingGain} onChange={(e) => setUnderstandingGain(e.target.value)} placeholder={language === "vi" ? "Ví dụ: Tôi đã hiểu rõ hơn mối quan hệ giữa hai khái niệm mà trước đó tôi còn nhầm..." : "Example: I now understand the relationship between two ideas I previously confused..."} /></label>
          <label className="field-block compact-field"><span>{language === "vi" ? "Nguyên nhân chính của lỗi/điểm chưa chắc" : "Main cause of the error/uncertainty"}</span><select value={errorCause} onChange={(e) => setErrorCause(e.target.value)}><option value="">{language === "vi" ? "Chọn một nguyên nhân" : "Choose one cause"}</option>{errorCauseOptions.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
          <label className="field-block"><span>{language === "vi" ? "Giải thích lại ý đúng bằng lời của bạn" : "Restate the corrected idea in your own words"}</span><textarea value={correctedExplanation} onChange={(e) => setCorrectedExplanation(e.target.value)} placeholder={language === "vi" ? "Không sao chép đáp án. Hãy nối nguyên nhân và hệ quả bằng cách bạn hiểu." : "Do not copy the answer. Connect cause and consequence in your own reasoning."} /></label>
          <label className="field-block"><span>{language === "vi" ? "Lần học tiếp theo bạn sẽ làm gì khác đi?" : "What will you do differently next time?"}</span><textarea value={actionPlan} onChange={(e) => setActionPlan(e.target.value)} placeholder={language === "vi" ? "Ví dụ: Tôi sẽ tự vẽ lại sơ đồ và giải thích bằng lời trước khi xem đáp án." : "Example: I will redraw the structure and explain it in my own words before checking an answer."} /></label>
          <div className="confidence-row"><span>{language === "vi" ? "Mức tự tin sau Rethink:" : "Confidence after Rethink:"}</span>{[1, 2, 3, 4, 5].map((value) => <button type="button" key={value} className={rethinkConfidence === value ? "confidence-button active" : "confidence-button"} onClick={() => setRethinkConfidence(value)}>{value}</button>)}</div>
        </section>

        {recommendation && <section className="rethink-section recommendation-card">
          <p className="eyebrow">{language === "vi" ? "Gợi ý cho bước tiếp theo" : "Recommended next action"}</p>
          <h3>{recommendation.title}</h3>
          <p>{recommendation.reason}</p>
          {(recommendation.weak_concepts?.length || 0) > 0 && <p className="muted">{language === "vi" ? "Khái niệm ưu tiên: " : "Priority concepts: "}{recommendation.weak_concepts.join(", ")}</p>}
        </section>}

        <div className="phase-actions">
          <button className="button secondary" onClick={() => saveRethink(false)} disabled={busy}>{phaseDone("RETHINK") ? (language === "vi" ? "Lưu thay đổi Rethink" : "Save Rethink changes") : (language === "vi" ? "Lưu Rethink" : "Save Rethink")}</button>
          {!phaseDone("RETHINK") && phase === "RETHINK" && <button className="button primary" disabled={busy || !rethinkCanComplete} onClick={() => saveRethink(true)}>{language === "vi" ? "Hoàn thành chu trình POWER" : "Complete POWER cycle"}</button>}
          {viewPhase !== phase && <button className="button primary" onClick={() => setViewPhase(phase)}>{language === "vi" ? `Trở lại ${phase}` : `Back to ${phase}`}</button>}
        </div>
      </>}
    </article>;
  };

  const quickActions = viewPhase === "PREPARE"
    ? [language === "vi" ? "Hỏi tôi một câu kiến thức nền" : "Ask me one prior-knowledge question", language === "vi" ? "Giúp tôi làm rõ mục tiêu" : "Help clarify my goal"]
    : viewPhase === "ORGANIZE"
      ? [language === "vi" ? "Gợi ý quan hệ giữa các khái niệm" : "Suggest concept relationships", language === "vi" ? "Cho tôi một bảng so sánh" : "Give me a comparison table"]
      : viewPhase === "RETHINK"
        ? [language === "vi" ? "Giúp tôi tìm nguyên nhân sai" : "Help identify why I was wrong", language === "vi" ? "Hỏi tôi một câu phản tư" : "Ask me a reflection question"]
        : [language === "vi" ? "Giải thích đơn giản hơn" : "Explain more simply", language === "vi" ? "So sánh hai khái niệm" : "Compare two concepts", language === "vi" ? "Kiểm tra tôi" : "Quiz me"];

  return (
    <AuthGuard>
      <AppShell>
        <div className="page-heading">
          <div><p className="eyebrow">{language === "vi" ? `Sinh học ${unitDetail?.grade ?? ""}` : `Biology ${unitDetail?.grade ?? ""}`} · POWER learning cycle</p><h1>{unitDetail ? (language === "vi" ? unitDetail.name_vi : unitDetail.name_en) : blueprint?.title}</h1>{unitDetail?.printed_page_start && <p className="muted">{language === "vi" ? `SGK: trang ${unitDetail.printed_page_start}${unitDetail.printed_page_end && unitDetail.printed_page_end !== unitDetail.printed_page_start ? `–${unitDetail.printed_page_end}` : ""}` : `Textbook: pp. ${unitDetail.printed_page_start}${unitDetail.printed_page_end && unitDetail.printed_page_end !== unitDetail.printed_page_start ? `–${unitDetail.printed_page_end}` : ""}`}</p>}</div>
          <div className="cycle-controls">
            {sessionHistory.length > 1 && <select aria-label={language === "vi" ? "Chọn chu trình POWER" : "Choose POWER cycle"} value={session?.id || ""} onChange={(e) => switchSession(e.target.value)}>
              {sessionHistory.map((item, index) => <option key={item.id} value={item.id}>{language === "vi" ? `Chu trình ${sessionHistory.length - index}` : `Cycle ${sessionHistory.length - index}`} · {item.status === "completed" ? (language === "vi" ? "đã hoàn thành" : "completed") : (language === "vi" ? "đang học" : "active")}</option>)}
            </select>}
            {session?.status === "completed" && <button className="button secondary inline" disabled={busy} onClick={startNewCycle}>{language === "vi" ? "Bắt đầu chu trình mới" : "Start new cycle"}</button>}
          </div>
        </div>
        <div className="power-stepper">
          {phases.map((p) => {
            const available = Boolean(session?.phases?.[p]) || p === phase;
            return <button type="button" key={p} disabled={!available} onClick={() => openPhase(p)} className={["power-step", p === viewPhase ? "active" : "", p === phase ? "current" : "", phaseDone(p) ? "done" : ""].filter(Boolean).join(" ")}>{phaseDone(p) ? "✓" : p[0]}<span>{p}</span></button>;
          })}
        </div>
        {viewPhase !== phase && <div className="review-banner">{language === "vi" ? `Chế độ xem lại: ${viewPhase}. Pha tiến trình hiện tại là ${phase}; việc xem lại không làm lùi tiến trình.` : `Review mode: ${viewPhase}. Current progression is ${phase}; reviewing does not move progress backward.`}</div>}
        {session?.status === "completed" && <div className="review-banner complete-cycle">{language === "vi" ? "Chu trình này đã hoàn thành. Bạn có thể bấm P–O–W–E–R để xem lại từng pha, chỉnh sửa Prepare/Organize, hoặc bắt đầu một chu trình mới." : "This cycle is complete. Use P–O–W–E–R to review each phase, edit Prepare/Organize, or start a new cycle."}</div>}
        {notice && <div className="notice-banner">{notice}</div>}
        {sessionBusy ? <div className="card loading-card">{language === "vi" ? "Đang mở phiên POWER…" : "Opening POWER session…"}</div> : <div className="lesson-layout">
          {viewPhase === "PREPARE" && renderPrepare()}
          {viewPhase === "ORGANIZE" && renderOrganize()}
          {viewPhase === "WORK" && renderWork()}
          {viewPhase === "EVALUATE" && renderEvaluate()}
          {viewPhase === "RETHINK" && renderRethink()}
          <aside className="tutor-card">
            <div className="tutor-header"><div><span className="pill">POWER Tutor · {viewPhase}</span><h3>{language === "vi" ? "Hỗ trợ đúng pha học tập" : "Phase-aware learning support"}</h3></div></div>
            {tutorProvider && <div><span className="pill">{tutorProvider === "openai" ? "OpenAI" : "Mock"}</span> <span className="muted">{language === "vi" ? `Retrieval: ${retrievalCount ?? 0} đoạn` : `Retrieval: ${retrievalCount ?? 0} chunks`}</span></div>}
            {tutorProvider === "mock" && <p className="muted">{language === "vi" ? "Tutor đang chạy mock mode. Hãy dùng AI_PROVIDER=openai để kiểm thử Tutor thật." : "Tutor is running in mock mode. Use AI_PROVIDER=openai to test the real Tutor."}</p>}
            <div className="quick-actions">{quickActions.map((x) => <button key={x} onClick={() => setMessage(x)}>{x}</button>)}</div>
            {blocks.length > 0 && <PowerTutorRenderer blocks={blocks} />}
            <div className="tutor-input"><textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder={language === "vi" ? `Hỏi POWER trong pha ${viewPhase}…` : `Ask POWER during ${viewPhase}…`} /><button className="button primary" disabled={busy || !session} onClick={askTutor}>{busy ? "…" : (language === "vi" ? "Gửi" : "Send")}</button></div>
          </aside>
        </div>}
      </AppShell>
    </AuthGuard>
  );
}
