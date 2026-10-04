"use client";

import { useEffect } from "react";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("POWER UI error", error);
  }, [error]);

  return (
    <div className="center-page">
      <div className="status-panel status-error">
        <strong>POWER gặp lỗi khi mở màn hình này</strong>
        <p>{error.message || "Unexpected application error"}</p>
        <button className="button primary" onClick={reset}>Thử lại</button>
      </div>
    </div>
  );
}
