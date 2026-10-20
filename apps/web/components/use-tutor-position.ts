"use client";

import { useEffect, useRef, useState, type KeyboardEvent, type PointerEvent } from "react";

type Point = { x: number; y: number };
type Target = "launcher" | "popup";
type Bounds = { left: number; top: number; right: number; bottom: number };
const STORAGE_KEY = "power-tutor-position-v1";
const ICON_SIZE = 60;
const GAP = 12;

function bounds(): Bounds {
  const viewport = window.visualViewport;
  const left = viewport?.offsetLeft ?? 0;
  const top = viewport?.offsetTop ?? 0;
  const right = left + (viewport?.width ?? document.documentElement.clientWidth);
  let bottom = top + (viewport?.height ?? window.innerHeight);
  const dock = document.querySelector(".study-dock")?.getBoundingClientRect();
  // Keep the timer's whole horizontal band available, even after dragging.
  if (dock && dock.top > top + ICON_SIZE + GAP * 2) bottom = Math.min(bottom, dock.top);
  return { left: left + GAP, top: top + GAP, right: right - GAP, bottom: bottom - GAP };
}

function size(target: Target, area: Bounds) {
  return target === "launcher" ? { width: ICON_SIZE, height: ICON_SIZE }
    : { width: Math.min(440, area.right - area.left), height: Math.min(630, area.bottom - area.top) };
}

function clamp(point: Point, target: Target, area = bounds()): Point {
  const { width, height } = size(target, area);
  return { x: Math.max(area.left, Math.min(point.x, area.right - width)),
    y: Math.max(area.top, Math.min(point.y, area.bottom - height)) };
}

export function useTutorPosition(open: boolean) {
  const [icon, setIcon] = useState<Point | null>(null);
  const [popup, setPopup] = useState<Point | null>(null);
  const [area, setArea] = useState<Bounds | null>(null);
  const [dragging, setDragging] = useState<Target | null>(null);
  const drag = useRef<{ pointerId: number; target: Target; start: Point; origin: Point; moved: boolean } | null>(null);
  const suppressClick = useRef(false);

  useEffect(() => {
    let stored: Point | null = null;
    try {
      const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
      if (value && Number.isFinite(value.x) && Number.isFinite(value.y)) stored = value;
    } catch { /* Storage is optional, including private browsing. */ }
    const fit = () => {
      const next = bounds();
      setArea(next);
      setIcon(previous => clamp(previous || stored || { x: next.right - ICON_SIZE, y: next.bottom - ICON_SIZE }, "launcher", next));
      setPopup(previous => previous && clamp(previous, "popup", next));
    };
    fit();
    window.addEventListener("resize", fit);
    window.visualViewport?.addEventListener("resize", fit);
    window.visualViewport?.addEventListener("scroll", fit);
    const observer = new ResizeObserver(fit);
    const dock = document.querySelector(".study-dock");
    if (dock) observer.observe(dock);
    return () => {
      window.removeEventListener("resize", fit);
      window.visualViewport?.removeEventListener("resize", fit);
      window.visualViewport?.removeEventListener("scroll", fit);
      observer.disconnect();
    };
  }, []);

  useEffect(() => {
    if (!icon) return;
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(icon)); } catch { /* Optional preference. */ }
  }, [icon]);

  useEffect(() => {
    if (!open || !icon) return;
    const next = bounds();
    const panel = size("popup", next);
    setPopup(clamp({ x: icon.x + ICON_SIZE - panel.width, y: icon.y - GAP - panel.height }, "popup", next));
    // Re-anchor only when opening. Header dragging then controls the popup independently.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const move = (target: Target, point: Point) => {
    const next = clamp(point, target);
    if (target === "launcher") setIcon(next); else setPopup(next);
  };
  const pointerDown = (target: Target, event: PointerEvent<HTMLElement>) => {
    if (!event.isPrimary || event.button !== 0 || (target === "popup" && (event.target as HTMLElement).closest("button"))) return;
    const rect = event.currentTarget.getBoundingClientRect();
    suppressClick.current = false;
    drag.current = { pointerId: event.pointerId, target, start: { x: event.clientX, y: event.clientY }, origin: { x: rect.left, y: rect.top }, moved: false };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const pointerMove = (event: PointerEvent<HTMLElement>) => {
    const current = drag.current;
    if (!current || current.pointerId !== event.pointerId) return;
    const dx = event.clientX - current.start.x;
    const dy = event.clientY - current.start.y;
    if (!current.moved && Math.hypot(dx, dy) < 6) return;
    current.moved = true;
    suppressClick.current = true;
    setDragging(current.target);
    move(current.target, { x: current.origin.x + dx, y: current.origin.y + dy });
  };
  const pointerEnd = (event: PointerEvent<HTMLElement>) => {
    if (drag.current?.pointerId !== event.pointerId) return;
    if (event.type !== "pointerup") suppressClick.current = false;
    drag.current = null;
    setDragging(null);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
  };
  const keyMove = (event: KeyboardEvent<HTMLElement>, target: Target) => {
    const direction: Record<string, Point> = { ArrowLeft: { x: -20, y: 0 }, ArrowRight: { x: 20, y: 0 }, ArrowUp: { x: 0, y: -20 }, ArrowDown: { x: 0, y: 20 } };
    const delta = direction[event.key];
    const current = target === "launcher" ? icon : popup;
    if (!delta || !current) return;
    event.preventDefault();
    move(target, { x: current.x + delta.x, y: current.y + delta.y });
  };
  const dragProps = (target: Target) => ({
    onPointerDown: (event: PointerEvent<HTMLElement>) => pointerDown(target, event),
    onPointerMove: pointerMove, onPointerUp: pointerEnd, onPointerCancel: pointerEnd,
    onLostPointerCapture: pointerEnd,
    onKeyDown: (event: KeyboardEvent<HTMLElement>) => { if (event.target === event.currentTarget) keyMove(event, target); },
  });

  return { dragging, dragProps,
    consumeDragClick: () => { const suppressed = suppressClick.current; suppressClick.current = false; return suppressed; },
    iconStyle: icon ? { left: icon.x, top: icon.y, right: "auto", bottom: "auto" } : undefined,
    popupStyle: popup && area ? { left: popup.x, top: popup.y, right: "auto", bottom: "auto", ...size("popup", area) } : undefined,
  };
}
