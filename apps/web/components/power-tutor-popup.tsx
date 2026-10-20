"use client";

import { useEffect, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";
import { PowerTutorRenderer, type PowerTutorBlock } from "./power-tutor-renderer";

export type TutorPhase = "PREPARE" | "ORGANIZE" | "WORK" | "EVALUATE" | "RETHINK";
export type TutorFeedbackRequest = { id: number; sessionId: string; phase: TutorPhase; message: string };
type Turn = { role: "user" | "assistant"; text: string; blocks?: PowerTutorBlock[]; image?: string };
type Attachment = { name: string; dataUrl: string };

export function PowerTutorPopup({ sessionId, phase, language, conceptCode, feedbackRequest, onBusyChange }: {
  sessionId: string;
  phase: TutorPhase;
  language: "vi" | "en";
  conceptCode?: string | null;
  feedbackRequest: TutorFeedbackRequest | null;
  onBusyChange: (busy: boolean) => void;
}) {
  const vi = language === "vi";
  const threadKey = `${sessionId}:${phase}`;
  const [open, setOpen] = useState(false);
  const [threads, setThreads] = useState<Record<string, Turn[]>>({});
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [attachments, setAttachments] = useState<Record<string, Attachment | undefined>>({});
  const [pending, setPending] = useState<{ key: string; text: string } | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [imageBusy, setImageBusy] = useState(false);
  const inFlight = useRef(false);
  const handledRequest = useRef<number | null>(null);
  const launcher = useRef<HTMLButtonElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const messages = useRef<HTMLDivElement>(null);
  const draft = drafts[threadKey] || "";
  const turns = threads[threadKey] || [];
  const attachment = attachments[threadKey];
  const busy = pending !== null;
  const setDraft = (value: string) => setDrafts(previous => ({ ...previous, [threadKey]: value }));
  const close = () => { setOpen(false); launcher.current?.focus(); };

  useEffect(() => {
    if (open) composer.current?.focus();
  }, [open, threadKey]);
  useEffect(() => {
    if (messages.current) messages.current.scrollTop = messages.current.scrollHeight;
  }, [open, threadKey, threads, pending, errors]);

  const send = async (explicitMessage?: string, illustration = false) => {
    if (inFlight.current) return;
    const image = explicitMessage === undefined && !illustration ? attachment : undefined;
    const text = (explicitMessage ?? draft).trim() || (image
      ? (vi ? "Hãy phân tích hình ảnh Sinh học này và giúp tôi hiểu nó." : "Analyze this Biology image and help me understand it.") : "");
    if (!text || !sessionId) return;
    const key = threadKey;
    inFlight.current = true;
    onBusyChange(true);
    setOpen(true);
    setImageBusy(illustration);
    setPending({ key, text });
    setErrors(previous => ({ ...previous, [key]: "" }));
    if (explicitMessage !== undefined) setDrafts(previous => ({ ...previous, [key]: text }));
    try {
      let reply: Turn;
      const context = { concept_code: conceptCode || undefined, language, power_session_id: sessionId, phase };
      if (illustration) {
        const result = await apiFetch<{ image_data_url: string }>("/tutor/generate-image", {
          method: "POST", body: JSON.stringify({ ...context, prompt: text }),
        });
        reply = { role: "assistant", text: vi ? "Hình minh họa do AI tạo. Hãy đối chiếu với học liệu." : "AI-generated illustration. Check it against your learning materials.", image: result.image_data_url };
      } else {
        const result = await apiFetch<{ blocks: PowerTutorBlock[] }>("/tutor/respond", {
          method: "POST",
          body: JSON.stringify({ ...context, message: text, image_data_url: image?.dataUrl || null,
            conversation: turns.filter(turn => !turn.image).slice(-8).map(turn => ({ role: turn.role, content: turn.text.slice(0, 4000) })),
          }),
        });
        if (!result.blocks?.length) throw new Error(vi ? "Tutor chưa trả về phản hồi. Hãy thử gửi lại." : "Tutor returned no response. Please try again.");
        const replyText = result.blocks.map(block => block.type === "text" ? String(block.content) : JSON.stringify(block)).join("\n");
        reply = { role: "assistant", text: replyText, blocks: result.blocks };
      }
      setThreads(previous => ({ ...previous, [key]: [...(previous[key] || []), { role: "user", text: text + (image ? `\n[${image.name}]` : "") } as Turn, reply].slice(-40) }));
      setDrafts(previous => ({ ...previous, [key]: previous[key]?.trim() === text ? "" : previous[key] || "" }));
      if (image) setAttachments(previous => ({ ...previous, [key]: previous[key] === image ? undefined : previous[key] }));
    } catch (error) {
      setErrors(previous => ({ ...previous, [key]: error instanceof Error ? error.message : (vi ? "Không thể kết nối Tutor. Hãy thử lại." : "Unable to reach Tutor. Please try again.") }));
    } finally {
      setPending(null);
      setImageBusy(false);
      inFlight.current = false;
      onBusyChange(false);
    }
  };

  useEffect(() => {
    if (!feedbackRequest || handledRequest.current === feedbackRequest.id
        || feedbackRequest.sessionId !== sessionId || feedbackRequest.phase !== phase) return;
    handledRequest.current = feedbackRequest.id;
    void send(feedbackRequest.message);
    // A request is consumed once, including React Strict Mode's effect replay.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [feedbackRequest, threadKey]);

  const attach = (file: File | undefined) => {
    if (!file) return;
    const key = threadKey;
    if (!["image/png", "image/jpeg", "image/webp"].includes(file.type) || file.size > 5 * 1024 * 1024) {
      setErrors(previous => ({ ...previous, [key]: vi ? "Chọn ảnh PNG, JPEG hoặc WebP không quá 5 MB." : "Choose a PNG, JPEG or WebP image up to 5 MB." }));
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        const dataUrl = reader.result;
        setAttachments(previous => ({ ...previous, [key]: { name: file.name, dataUrl } }));
        setOpen(true);
      }
    };
    reader.onerror = () => setErrors(previous => ({ ...previous, [key]: vi ? "Không đọc được ảnh." : "Unable to read the image." }));
    reader.readAsDataURL(file);
  };
  const suggestions = phase === "PREPARE"
    ? [vi ? "Giúp tôi làm rõ mục tiêu" : "Help clarify my goal", vi ? "Hỏi tôi một câu kiến thức nền" : "Ask me a prior-knowledge question"]
    : phase === "ORGANIZE"
      ? [vi ? "Gợi ý quan hệ giữa các khái niệm" : "Suggest concept relationships"]
      : phase === "RETHINK"
        ? [vi ? "Giúp tôi tìm nguyên nhân sai" : "Help identify why I was wrong"]
        : [vi ? "Giải thích đơn giản hơn" : "Explain more simply", vi ? "Kiểm tra tôi" : "Quiz me"];

  return <div className="power-tutor-widget">
    <button ref={launcher} type="button" className="power-tutor-launcher" aria-expanded={open} aria-controls="power-tutor-dialog"
      aria-label={vi ? "Mở POWER Tutor" : "Open POWER Tutor"} onClick={() => open ? close() : setOpen(true)}>
      <span aria-hidden="true">✦</span> POWER Tutor
    </button>
    {open && <section id="power-tutor-dialog" className="power-tutor-popup" role="dialog" aria-modal="false" aria-labelledby="power-tutor-title"
      onKeyDown={event => { if (event.key === "Escape") { event.stopPropagation(); close(); } }}>
      <header className="power-tutor-popup-head">
        <div><h2 id="power-tutor-title">POWER Tutor</h2><span>{phase} · {vi ? "Cùng bạn tìm lời giải" : "Think it through together"}</span></div>
        <button type="button" aria-label={vi ? "Thu gọn POWER Tutor" : "Minimize POWER Tutor"} onClick={close}>−</button>
      </header>
      <div ref={messages} className="power-tutor-messages" role="log" aria-live="polite" aria-label={vi ? "Hội thoại với POWER Tutor" : "Conversation with POWER Tutor"}>
        {!turns.length && !pending && <p className="muted">{vi ? "Bạn đang vướng ở đâu? Hãy thử giải thích trước, Tutor sẽ giúp bằng gợi ý và câu hỏi dẫn dắt." : "Where are you stuck? Try explaining first; your Tutor can offer hints and guiding questions."}</p>}
        {turns.map((turn, index) => <article key={index} className={`power-tutor-turn ${turn.role}`}>
          <strong>{turn.role === "user" ? (vi ? "Bạn" : "You") : "POWER Tutor"}</strong>
          {turn.blocks ? <PowerTutorRenderer blocks={turn.blocks} /> : <p>{turn.text}</p>}
          {turn.image && <img src={turn.image} alt={vi ? "Hình minh họa Sinh học do AI tạo" : "AI-generated Biology illustration"} />}
        </article>)}
        {pending?.key === threadKey && <><article className="power-tutor-turn user"><strong>{vi ? "Bạn" : "You"}</strong><p>{pending.text}</p></article><p role="status">{imageBusy ? (vi ? "Đang tạo hình minh họa…" : "Creating illustration…") : (vi ? "Tutor đang phản hồi…" : "Tutor is responding…")}</p></>}
      </div>
      {errors[threadKey] && <p className="power-tutor-error" role="alert">{errors[threadKey]}</p>}
      <div className="power-tutor-compose">
        <div className="quick-actions">{suggestions.map(text => <button key={text} onClick={() => { setDraft(text); composer.current?.focus(); }}>{text}</button>)}</div>
        {attachment && <div className="power-tutor-attachment">{attachment.name}<button type="button" onClick={() => setAttachments(previous => ({ ...previous, [threadKey]: undefined }))}>{vi ? "Bỏ ảnh" : "Remove"}</button></div>}
        <label className="sr-only" htmlFor="power-tutor-message">{vi ? "Tin nhắn cho POWER Tutor" : "Message POWER Tutor"}</label>
        <textarea ref={composer} id="power-tutor-message" value={draft} maxLength={12000} onChange={event => setDraft(event.target.value)}
          placeholder={vi ? "Viết câu hỏi của bạn…" : "Write your question…"}
          onKeyDown={event => { if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); void send(); } }} />
        <div className="power-tutor-compose-actions">
          <label className="button secondary">{vi ? "Đính kèm ảnh" : "Attach image"}<input aria-label={vi ? "Đính kèm ảnh cho Tutor" : "Attach image for Tutor"} type="file" accept="image/png,image/jpeg,image/webp" className="sr-only" onChange={event => { attach(event.target.files?.[0]); event.target.value = ""; }} /></label>
          <button type="button" className="button secondary" disabled={busy || !draft.trim() || draft.trim().length > 1200} onClick={() => void send(undefined, true)}>{vi ? "Tạo hình" : "Illustrate"}</button>
          <button type="button" className="button primary" disabled={busy || (!draft.trim() && !attachment)} onClick={() => void send()}>{busy ? "…" : (vi ? "Gửi" : "Send")}</button>
        </div>
        <small className="muted">{vi ? "AI có thể sai. Đối chiếu với học liệu. Hội thoại được giữ khi thu gọn trong lần mở trang này." : "AI can make mistakes. Check your sources. Conversations stay when minimized during this page visit."}</small>
      </div>
    </section>}
  </div>;
}
