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
  export_scope: string;
  datasets: Dataset[];
  counts: {
    users_total: number;
    event_count: number;
    cycle_count: number;
    mastery_snapshot_count: number;
    assessment_count: number;
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
              <div className="stat-card"><span>Lượt Practice / Evaluate</span><strong>{status.counts.assessment_count}</strong></div>
              <div className="stat-card"><span>Sự kiện đã ghi</span><strong>{status.counts.event_count}</strong></div>
            </div>
            <section className="hero-card" style={{ display: "block", marginTop: 20 }}>
              <h2>Xuất dữ liệu hành vi học tập</h2>
              <p>Xuất tất cả bản ghi hành vi trong khoảng ngày đã chọn, bao gồm dữ liệu lịch sử; không cần nhập consent hoặc có phản hồi Google Form. Mỗi tệp gồm nhiều học sinh, tối đa 10.000 dòng mỗi lượt.</p>
              <div style={{ display: "grid", gap: 12, maxWidth: 560 }}>
                <label>Dataset <select value={dataset} onChange={e => {setDataset(e.target.value as Dataset); setOffset(0);}}>
                  {status.datasets.map(d => <option key={d} value={d}>{labels[d]}</option>)}
                </select></label>
                <p className="muted">Chọn khoảng ngày tối đa 366 ngày mỗi lượt. Để lấy hết lịch sử dài hơn, tải lần lượt các khoảng ngày liền nhau.</p>
                <label>Từ ngày <input type="date" value={from} onChange={e => {setFrom(e.target.value); setOffset(0);}} /></label>
                <label>Đến ngày (không gồm ngày này) <input type="date" value={to} onChange={e => {setTo(e.target.value); setOffset(0);}} /></label>
                <label>Bỏ qua bao nhiêu dòng (tải phân trang) <input type="number" value={offset} min={0} step={10000} onChange={e => setOffset(Math.max(0, Number(e.target.value) || 0))} /></label>
                <button className="button primary inline" disabled={busy || !from || !to || from >= to} onClick={download}>
                  {busy ? "Đang xử lý…" : "Tải CSV có kiểm soát"}
                </button>
              </div>
              <small className="muted">CSV hành vi dùng mã người tham gia, không chứa email, nội dung hội thoại hoặc câu trả lời tự do. Tệp Email ↔ Participant ID chỉ gồm tài khoản có hoạt động trong khoảng ngày đã chọn; lưu riêng và không công khai. Dữ liệu chỉ phục vụ nghiên cứu và cải tiến sản phẩm.</small>
            </section>
          </>
        )}
      </AppShell>
    </AuthGuard>
  );
}
