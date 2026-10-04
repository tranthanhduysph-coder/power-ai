"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { AuthGuard } from "@/components/auth-guard";
import { useAuth } from "@/components/auth-provider";
import { useLanguage } from "@/components/language-provider";
import { apiFetch } from "@/lib/api";

type CatalogNode = {
  code: string;
  name_vi: string;
  name_en: string;
  unit_type: "part" | "chapter" | "lesson" | "practice" | "project" | "legacy";
  lesson_number: number | null;
  printed_page_start: number | null;
  printed_page_end: number | null;
  is_power_ready: boolean;
  children: CatalogNode[];
};

type CatalogGrade = { grade: number; items: CatalogNode[] };


function countReady(nodes: CatalogNode[]): number {
  return nodes.reduce((total, node) => total + (node.is_power_ready ? 1 : 0) + countReady(node.children || []), 0);
}

function LessonRow({ node, language }: { node: CatalogNode; language: "vi" | "en" }) {
  const name = language === "vi" ? node.name_vi : node.name_en;
  const pageLabel = node.printed_page_start
    ? `${node.printed_page_start}${node.printed_page_end && node.printed_page_end !== node.printed_page_start ? `–${node.printed_page_end}` : ""}`
    : null;
  return (
    <div className={node.is_power_ready ? "catalog-lesson ready" : "catalog-lesson"}>
      <div>
        <div className="catalog-lesson-title">
          {node.lesson_number ? <span className="catalog-lesson-number">{node.lesson_number}</span> : null}
          <strong>{name}</strong>
        </div>
        <div className="catalog-lesson-meta">
          {pageLabel && <span>{language === "vi" ? `SGK tr. ${pageLabel}` : `Textbook pp. ${pageLabel}`}</span>}
          <span>{node.unit_type === "practice" ? (language === "vi" ? "Thực hành" : "Lab") : node.unit_type === "project" ? (language === "vi" ? "Dự án" : "Project") : (language === "vi" ? "Bài học" : "Lesson")}</span>
        </div>
      </div>
      {node.is_power_ready ? (
        <Link className="button primary inline" href={`/learn/${encodeURIComponent(node.code)}`}>
          {language === "vi" ? "Học bằng POWER" : "Learn with POWER"}
        </Link>
      ) : (
        <span className="pill muted-pill">{language === "vi" ? "Chưa nạp POWER" : "POWER content pending"}</span>
      )}
    </div>
  );
}

function CatalogNodeView({ node, language }: { node: CatalogNode; language: "vi" | "en" }) {
  if (["lesson", "practice", "project"].includes(node.unit_type)) {
    return <LessonRow node={node} language={language} />;
  }
  return (
    <section className={node.unit_type === "part" ? "catalog-part" : "catalog-chapter"}>
      <div className="catalog-group-heading">
        <span className="eyebrow">{node.unit_type === "part" ? (language === "vi" ? "PHẦN" : "PART") : (language === "vi" ? "CHƯƠNG" : "CHAPTER")}</span>
        <h3>{language === "vi" ? node.name_vi : node.name_en}</h3>
      </div>
      <div className="catalog-children">
        {node.children.map((child) => <CatalogNodeView key={child.code} node={child} language={language} />)}
      </div>
    </section>
  );
}

export default function LearnCatalogPage() {
  const { language } = useLanguage();
  const { user, devMode, loading } = useAuth();
  const [grades, setGrades] = useState<CatalogGrade[]>([]);
  const [selectedGrade, setSelectedGrade] = useState(12);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (loading || (!devMode && !user)) return;
    apiFetch<{ grades: CatalogGrade[] }>("/catalog/tree")
      .then((res) => setGrades(res.grades))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load curriculum"));
  }, [loading, devMode, user]);

  const current = grades.find((g) => g.grade === selectedGrade);
  const readyCount = current ? countReady(current.items) : 0;

  return (
    <AuthGuard>
      <AppShell>
        <div className="page-heading">
          <div>
            <p className="eyebrow">POWER Biology · Curriculum</p>
            <h1>{language === "vi" ? "Chọn bài học" : "Choose a lesson"}</h1>
            <p className="muted">{language === "vi" ? "Danh mục Sinh học 10–12 được đọc từ database. Bài có nhãn POWER đã sẵn sàng để chạy đủ chu trình P–O–W–E–R." : "The Biology 10–12 catalog is database-driven. Lessons marked POWER are ready for the full P–O–W–E–R cycle."}</p>
          </div>
        </div>
        <div className="grade-tabs">
          {[10, 11, 12].map((grade) => <button key={grade} className={selectedGrade === grade ? "grade-tab active" : "grade-tab"} onClick={() => setSelectedGrade(grade)}>{language === "vi" ? `Sinh học ${grade}` : `Biology ${grade}`}</button>)}
        </div>
        {error && <div className="notice-banner">{error}</div>}
        <div className="catalog-summary card">
          <strong>{language === "vi" ? `Sinh học ${selectedGrade}` : `Biology ${selectedGrade}`}</strong>
          <span>{language === "vi" ? `${readyCount} bài đã nạp POWER` : `${readyCount} POWER-ready lesson(s)`}</span>
        </div>
        <div className="curriculum-catalog">
          {current?.items.map((node) => <CatalogNodeView key={node.code} node={node} language={language} />)}
          {!current && <div className="card loading-card">{language === "vi" ? "Đang tải chương trình…" : "Loading curriculum…"}</div>}
        </div>
      </AppShell>
    </AuthGuard>
  );
}
