"use client";

import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { useAuth } from "@/components/auth-provider";
import { apiBaseUrl, apiFetch } from "@/lib/api";
import { auth } from "@/lib/firebase";

type Dataset = "events" | "cycles" | "assessments" | "mastery" | "linkage";
type Status = {
  access: string;
  datasets: Dataset[];
  counts: {
    users_total: number;
    event_count: number;
    cycle_count: number;
    mastery_snapshot_count: number;
    consented_students: number;
  };
};

const labels: Record<Dataset, string> = {
  events: "Hành vi POWER (không gồm nội dung hội thoại)",
  cycles: "Chu trình POWER",
  assessments: "Kết quả Practice / Evaluate",
  mastery: "Lịch sử mastery",
  linkage: "Email ↔ Participant ID (nhạy cảm)",
};

function localDate(daysFromNow: number): string {
  const d = new Date();
  d.setDate(d.getDate() + daysFromNow);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export default function ResearchPage() {
  const { user, loading } = useAuth();
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [dataset, setDataset] = useState<Dataset>("cycles");
  const [from, setFrom] = useState(() => localDate(-30));
  const [to, setTo] = useState(() => localDate(1));
  const [offset, setOffset] = useState(0);
  const [email, setEmail] = useState("");
  const [responseRef, setResponseRef] = useState("");
  const [surveyVersion, setSurveyVersion] = useState("POWER-AI-WEB V5");
  const [consentedAt, setConsentedAt] = useState("");
  const [scopeStartAt, setScopeStartAt] = useState("");
  const [researchAllowed, setResearchAllowed] = useState(true);
  const [improvementAllowed, setImprovementAllowed] = useState(false);
  const [historicalConfirmed, setHistoricalConfirmed] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setStatus(await apiFetch<Status>("/research/status"));
      setError("");
    } catch (e) {
      setStatus(null);
      setError(e instanceof Error ? e.message : "Không thể xác thực Research Admin");
    }
  }, []);

  useEffect(() => {
    if (!loading && user) refresh();
  }, [loading, user, refresh]);

  const download = async () => {
    if (!auth.currentUser) return;
    if (dataset === "linkage" && !window.confirm(
      "Tệp này chứa email học sinh. Chỉ tải khi cần ghép Google Form; lưu trữ riêng và không chia sẻ. Tiếp tục?"
    )) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const token = await auth.currentUser.getIdToken();
      const qs = new URLSearchParams({
        start_at: new Date(from + "T00:00:00").toISOString(),
        end_at: new Date(to + "T00:00:00").toISOString(),
        limit: "10000",
        offset: String(offset),
      });
      const res = await fetch(`${apiBaseUrl}/research/exports/${dataset}?${qs}`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Lỗi xuất dữ liệu: ${res.status}`);
      }
      const url = URL.createObjectURL(await res.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = `power_research_${dataset}_${from}_to_${to}_offset${offset}.csv`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setNotice("Đã xuất CSV và ghi audit log. Nếu có 10.000 dòng, tăng offset để tải phần tiếp theo.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không thể tải dữ liệu");
    } finally {
      setBusy(false);
    }
  };

  const registerConsent = async () => {
    if (!responseRef.trim() || !consentedAt.trim() || !email.trim()) {
      setError("Phải có email đăng nhập, mã phản hồi Google Form và thời điểm đồng thuận.");
      return;
    }
    if (!window.confirm("Xác nhận đã đối chiếu lựa chọn đồng ý trong Google Form gốc?")) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await apiFetch("/research/consents", {
        method: "POST",
        body: JSON.stringify({
          email,
          survey_response_ref: responseRef,
          survey_version: surveyVersion,
          consented_at: new Date(consentedAt).toISOString(),
          activity_scope_start_at: scopeStartAt ? new Date(scopeStartAt).toISOString() : null,
          research_allowed: researchAllowed,
          improvement_allowed: improvementAllowed,
          historical_coverage_confirmed: historicalConfirmed,
        }),
      });
      setNotice("Đã đối chiếu tài khoản và lưu consent cùng audit log.");
      setResponseRef("");
      setEmail("");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không thể lưu consent");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthGuard>
      <AppShell>
        <div className="page-heading">
          <div>
            <p className="eyebrow">POWER Research Analytics</p>
            <h1>Quản trị dữ liệu nghiên cứu</h1>
            <p>Chỉ dành cho Research Admin đã xác thực Firebase UID và email.</p>
          </div>
        </div>

        {error && <div className="notice-banner error-notice">{error}</div>}
        {notice && <div className="notice-banner">{notice}</div>}
        {!status ? (
          <section className="hero-card">
            <p>Chưa có quyền truy cập hoặc chưa cấu hình Research Admin trên backend.</p>
            <button className="button primary inline" onClick={refresh}>Kiểm tra lại</button>
          </section>
        ) : (
          <>
            <div className="grid-3">
              <div className="stat-card"><span>Tài khoản</span><strong>{status.counts.users_total}</strong></div>
              <div className="stat-card"><span>Consent nghiên cứu hợp lệ</span><strong>{status.counts.consented_students}</strong></div>
              <div className="stat-card"><span>Sự kiện đã ghi</span><strong>{status.counts.event_count}</strong></div>
            </div>
            <section className="hero-card" style={{ display: "block", marginTop: 20 }}>
              <h2>1. Nhập quyết định consent từ Google Form</h2>
              <p>Chỉ nhập sau khi kiểm tra phản hồi gốc. Không suy diễn consent từ email hoặc việc sử dụng ứng dụng.</p>
              <div style={{ display: "grid", gap: 10, maxWidth: 560 }}>
                <label>Email đăng nhập POWER <input value={email} onChange={e => setEmail(e.target.value)} type="email" placeholder="student@example.com" /></label>
                <label>Mã phản hồi Form / dòng Sheet kiểm chứng <input value={responseRef} onChange={e => setResponseRef(e.target.value)} placeholder="form-id:response-id" /></label>
                <label>Phiên bản questionnaire <input value={surveyVersion} onChange={e => setSurveyVersion(e.target.value)} /></label>
                <label>Thời điểm consent (có múi giờ) <input value={consentedAt} onChange={e => setConsentedAt(e.target.value)} placeholder="2026-10-17T20:00:00+07:00" /></label>
                <label>Ngày bắt đầu dữ liệu được đồng ý dùng (tùy chọn) <input value={scopeStartAt} onChange={e => setScopeStartAt(e.target.value)} placeholder="Để trống nếu chỉ dùng log từ lúc consent" /></label>
                <label><input type="checkbox" checked={researchAllowed} onChange={e => setResearchAllowed(e.target.checked)} /> Đồng ý sử dụng dữ liệu cho nghiên cứu</label>
                <label><input type="checkbox" checked={improvementAllowed} onChange={e => setImprovementAllowed(e.target.checked)} /> Đồng ý sử dụng dữ liệu cho cải tiến sản phẩm</label>
                <label><input type="checkbox" checked={historicalConfirmed} onChange={e => setHistoricalConfirmed(e.target.checked)} /> Có bằng chứng đồng ý sử dụng lịch sử trước ngày consent (nếu khai báo)</label>
                <button className="button primary inline" disabled={busy} onClick={registerConsent}>Lưu bản ghi có kiểm chứng</button>
              </div>
            </section>
            <section className="hero-card" style={{ display: "block", marginTop: 20 }}>
              <h2>2. Xuất dữ liệu phục vụ nghiên cứu</h2>
              <p>Mặc định chỉ xuất học sinh đã đồng thuận, ẩn email và nội dung tương tác. Linkage CSV là tệp nhạy cảm riêng.</p>
              <div style={{ display: "grid", gap: 12, maxWidth: 560 }}>
                <label>Dataset <select value={dataset} onChange={e => {setDataset(e.target.value as Dataset); setOffset(0);}}>
                  {status.datasets.map(d => <option key={d} value={d}>{labels[d]}</option>)}
                </select></label>
                <label>Từ ngày <input type="date" value={from} onChange={e => setFrom(e.target.value)} /></label>
                <label>Đến ngày (không gồm ngày này) <input type="date" value={to} onChange={e => setTo(e.target.value)} /></label>
                <label>Bỏ qua bao nhiêu dòng (tải phân trang) <input type="number" value={offset} min={0} step={10000} onChange={e => setOffset(Math.max(0, Number(e.target.value) || 0))} /></label>
                <button className="button primary inline" disabled={busy || !from || !to || from >= to} onClick={download}>
                  {busy ? "Đang xử lý…" : "Tải CSV có kiểm soát"}
                </button>
              </div>
              <small className="muted">Lưu tệp linkage riêng. Không công khai CSV có email học sinh; không dùng dữ liệu khi consent bị rút.</small>
            </section>
          </>
        )}
      </AppShell>
    </AuthGuard>
  );
}
