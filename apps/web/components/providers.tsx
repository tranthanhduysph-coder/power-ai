"use client";

import { useEffect, useMemo, useState } from "react";
import { AuthProvider } from "./auth-provider";
import { LanguageProvider } from "./language-provider";

type ThemeMode = "light" | "dark";

const THEME_STORAGE_KEY = "power-ai-web:theme";
const TIMER_STORAGE_KEY = "power-ai-web:study-timer";

function formatTime(totalSeconds: number) {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return [hours, minutes, seconds].map((value) => String(value).padStart(2, "0")).join(":");
}

function ExperienceEnhancements({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<ThemeMode | null>(null);
  const [accumulatedSeconds, setAccumulatedSeconds] = useState(0);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [running, setRunning] = useState(false);
  const [now, setNow] = useState(Date.now());
  const [aboutOpen, setAboutOpen] = useState(false);
  const [termsOpen, setTermsOpen] = useState(false);

  useEffect(() => {
    const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY) as ThemeMode | null;
    const initialTheme: ThemeMode =
      savedTheme === "light" || savedTheme === "dark"
        ? savedTheme
        : window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";

    setTheme(initialTheme);
    document.documentElement.dataset.theme = initialTheme;
    document.documentElement.style.colorScheme = initialTheme;

    try {
      const savedTimer = JSON.parse(window.localStorage.getItem(TIMER_STORAGE_KEY) || "null") as
        | { accumulatedSeconds?: number; startedAt?: number | null; running?: boolean }
        | null;

      if (savedTimer) {
        setAccumulatedSeconds(Math.max(0, Number(savedTimer.accumulatedSeconds) || 0));
        setStartedAt(typeof savedTimer.startedAt === "number" ? savedTimer.startedAt : null);
        setRunning(Boolean(savedTimer.running && typeof savedTimer.startedAt === "number"));
      }
    } catch {
      window.localStorage.removeItem(TIMER_STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    if (!theme) return;
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    if (!running || startedAt === null) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [running, startedAt]);

  useEffect(() => {
    window.localStorage.setItem(
      TIMER_STORAGE_KEY,
      JSON.stringify({ accumulatedSeconds, startedAt, running }),
    );
  }, [accumulatedSeconds, startedAt, running]);

  const elapsedSeconds =
    accumulatedSeconds +
    (running && startedAt !== null ? Math.max(0, Math.floor((now - startedAt) / 1000)) : 0);

  const bioMessage = useMemo(() => {
    const messages = [
      "Ty thể đang cấp ATP cho phiên học này ⚡",
      "Neuron đã online. Đừng để nó chờ lâu 🧠",
      "Ribosome vẫn đang làm việc — mình cũng vậy nhé.",
      "DNA không tự nhân đôi vì deadline, nhưng chúng ta thì có thể chủ động 🧬",
    ];
    return messages[Math.floor(elapsedSeconds / 60) % messages.length];
  }, [elapsedSeconds]);

  const startTimer = () => {
    if (running) return;
    const timestamp = Date.now();
    setNow(timestamp);
    setStartedAt(timestamp);
    setRunning(true);
  };

  const pauseTimer = () => {
    if (!running || startedAt === null) return;
    const timestamp = Date.now();
    setAccumulatedSeconds((value) => value + Math.max(0, Math.floor((timestamp - startedAt) / 1000)));
    setNow(timestamp);
    setStartedAt(null);
    setRunning(false);
  };

  const resetTimer = () => {
    setAccumulatedSeconds(0);
    setStartedAt(null);
    setRunning(false);
    setNow(Date.now());
  };

  return (
    <>
      {children}

      <aside className="study-dock" aria-label="Công cụ phiên học">
        <div className="study-dock-bio" title={bioMessage}>
          <span aria-hidden="true">🧬</span>
          <span>{bioMessage}</span>
        </div>

        <div className="study-timer" aria-label="Đồng hồ học tập">
          <span className="study-timer-label">FOCUS</span>
          <strong>{formatTime(elapsedSeconds)}</strong>
          <div className="study-timer-actions">
            {!running ? (
              <button type="button" onClick={startTimer} aria-label="Bắt đầu đồng hồ học">
                ▶
              </button>
            ) : (
              <button type="button" onClick={pauseTimer} aria-label="Tạm dừng đồng hồ học">
                Ⅱ
              </button>
            )}
            <button type="button" onClick={resetTimer} aria-label="Đặt lại đồng hồ học">
              ↺
            </button>
          </div>
        </div>

        <button
          type="button"
          className="theme-toggle"
          onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
          aria-label={theme === "dark" ? "Chuyển sang chế độ sáng" : "Chuyển sang chế độ tối"}
          title={theme === "dark" ? "Chế độ sáng" : "Chế độ tối"}
        >
          <span aria-hidden="true">{theme === "dark" ? "☀" : "☾"}</span>
        </button>
      </aside>

      <footer className="site-footer">
        <div>
          <strong>© 2026 POWER-AI-WEB</strong>
          <span>Phát triển bởi ThS. Trần Thanh Duy</span>
        </div>
        <nav aria-label="Thông tin POWER-AI-WEB">
          <button type="button" onClick={() => setAboutOpen(true)}>
            Giới thiệu
          </button>
          <button type="button" onClick={() => setTermsOpen(true)}>
            Điều khoản &amp; Miễn trừ trách nhiệm
          </button>
        </nav>
      </footer>

      {aboutOpen && (
        <div className="info-modal-backdrop" role="presentation" onMouseDown={() => setAboutOpen(false)}>
          <section
            className="info-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="power-about-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="info-modal-head">
              <div>
                <p className="eyebrow">POWER-AI-WEB</p>
                <h2 id="power-about-title">Giới thiệu</h2>
              </div>
              <button type="button" onClick={() => setAboutOpen(false)} aria-label="Đóng">
                ×
              </button>
            </div>
            <p>
              POWER-AI-WEB là nền tảng hỗ trợ tự học Sinh học theo chu trình POWER:
              Prepare – Organize – Work – Evaluate – Rethink.
            </p>
            <p>
              Hệ thống sử dụng trí tuệ nhân tạo để hỗ trợ gợi ý, phản hồi và cá nhân hóa quá trình
              học tập, đồng thời duy trì vai trò chủ động của người học trong từng giai đoạn.
            </p>
            <div className="bio-note">
              <span aria-hidden="true">🧬</span>
              <span>Học có chiến lược. Nghỉ có chủ đích. ATP không phải là vô hạn.</span>
            </div>
          </section>
        </div>
      )}

      {termsOpen && (
        <div className="info-modal-backdrop" role="presentation" onMouseDown={() => setTermsOpen(false)}>
          <section
            className="info-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="power-terms-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="info-modal-head">
              <div>
                <p className="eyebrow">POWER-AI-WEB</p>
                <h2 id="power-terms-title">Điều khoản &amp; Miễn trừ trách nhiệm</h2>
              </div>
              <button type="button" onClick={() => setTermsOpen(false)} aria-label="Đóng">
                ×
              </button>
            </div>
            <p>
              POWER-AI-WEB sử dụng trí tuệ nhân tạo để hỗ trợ học tập, cung cấp gợi ý, phản hồi và
              nội dung được cá nhân hóa. Nội dung do AI tạo có thể có sai sót hoặc chưa phù hợp trong
              một số tình huống và không nên được xem là nguồn thông tin duy nhất.
            </p>
            <p>
              Người học nên đối chiếu với sách giáo khoa, tài liệu học tập chính thức và hướng dẫn
              của giáo viên khi cần thiết. POWER-AI-WEB hỗ trợ quá trình học tập và không thay thế
              vai trò chuyên môn của giáo viên.
            </p>
            <p>
              Các nội dung liên quan đến sức khỏe, y khoa hoặc an toàn chỉ có giá trị tham khảo giáo
              dục và không thay thế tư vấn của chuyên gia có thẩm quyền. Người dùng chịu trách nhiệm
              đối với cách sử dụng thông tin và sản phẩm học tập được tạo ra từ nền tảng.
            </p>
            <p>
              POWER-AI-WEB sẽ tiếp tục cải tiến chất lượng nội dung và hệ thống phản hồi dựa trên quá
              trình thử nghiệm và sử dụng thực tế.
            </p>
          </section>
        </div>
      )}
    </>
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <LanguageProvider>
        <ExperienceEnhancements>{children}</ExperienceEnhancements>
      </LanguageProvider>
    </AuthProvider>
  );
}
