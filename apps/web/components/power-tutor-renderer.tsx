"use client";

import { Fragment, type ReactNode } from "react";

export type PowerTutorBlock =
  | { type: "text"; content: string }
  | { type: "table"; headers: string[]; rows: string[][] }
  | { type: "checkpoint"; prompt: string }
  | { type: "diagram"; title?: string; nodes?: string[]; arrows?: string[] }
  | { type: string; [key: string]: unknown };

function normalizeTutorText(value: string) {
  return value
    .replace(/\r\n?/g, "\n")
    .replace(/\t/g, " ")
    .replace(/[ \u00a0]+$/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function renderInline(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const pattern = /(\*\*[^*]+\*\*|__[^_]+__|\*[^*\n]+\*|_[^_\n]+_|`[^`]+`)/g;
  let cursor = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > cursor) parts.push(<Fragment key={key++}>{text.slice(cursor, match.index)}</Fragment>);
    const token = match[0];
    if ((token.startsWith("**") && token.endsWith("**")) || (token.startsWith("__") && token.endsWith("__"))) {
      parts.push(<strong key={key++}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("`") && token.endsWith("`")) {
      parts.push(<code key={key++}>{token.slice(1, -1)}</code>);
    } else {
      parts.push(<em key={key++}>{token.slice(1, -1)}</em>);
    }
    cursor = match.index + token.length;
  }
  if (cursor < text.length) parts.push(<Fragment key={key++}>{text.slice(cursor)}</Fragment>);
  return parts;
}

function RichTutorText({ content }: { content: string }) {
  const lines = normalizeTutorText(content).split("\n");
  const nodes: ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i].trim();
    if (!line) {
      i += 1;
      continue;
    }

    const heading = line.match(/^#{1,6}\s+(.+)$/);
    if (heading) {
      nodes.push(<h4 key={`h-${i}`}>{renderInline(heading[1])}</h4>);
      i += 1;
      continue;
    }

    if (/^[-*•]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*•]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*•]\s+/, ""));
        i += 1;
      }
      nodes.push(<ul key={`ul-${i}`}>{items.map((item, index) => <li key={index}>{renderInline(item)}</li>)}</ul>);
      continue;
    }

    if (/^\d+[.)]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+[.)]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+[.)]\s+/, ""));
        i += 1;
      }
      nodes.push(<ol key={`ol-${i}`}>{items.map((item, index) => <li key={index}>{renderInline(item)}</li>)}</ol>);
      continue;
    }

    if (/^>\s?/.test(line)) {
      const quote: string[] = [];
      while (i < lines.length && /^>\s?/.test(lines[i].trim())) {
        quote.push(lines[i].trim().replace(/^>\s?/, ""));
        i += 1;
      }
      nodes.push(<blockquote key={`q-${i}`}>{quote.map((item, index) => <Fragment key={index}>{index > 0 && <br />}{renderInline(item)}</Fragment>)}</blockquote>);
      continue;
    }

    if (/^(-{3,}|_{3,}|\*{3,})$/.test(line)) {
      nodes.push(<hr key={`hr-${i}`} />);
      i += 1;
      continue;
    }

    const paragraph: string[] = [line];
    i += 1;
    while (i < lines.length) {
      const next = lines[i].trim();
      if (!next || /^#{1,6}\s+/.test(next) || /^[-*•]\s+/.test(next) || /^\d+[.)]\s+/.test(next) || /^>\s?/.test(next)) break;
      paragraph.push(next);
      i += 1;
    }
    nodes.push(
      <p key={`p-${i}`}>
        {paragraph.map((part, index) => (
          <Fragment key={index}>{index > 0 && <br />}{renderInline(part)}</Fragment>
        ))}
      </p>,
    );
  }

  return <div className="tutor-rich-text">{nodes}</div>;
}

export function PowerTutorRenderer({ blocks }: { blocks: PowerTutorBlock[] }) {
  return (
    <div className="tutor-blocks" aria-live="polite">
      {blocks.map((block, index) => {
        if (block.type === "text" && typeof block.content === "string") {
          return <RichTutorText key={index} content={block.content} />;
        }
        if (block.type === "table" && Array.isArray(block.headers) && Array.isArray(block.rows)) {
          return (
            <div className="table-scroll tutor-table" key={index}>
              <table>
                <thead><tr>{block.headers.map((header, i) => <th key={i}>{header}</th>)}</tr></thead>
                <tbody>{block.rows.map((row, r) => <tr key={r}>{row.map((cell: string, c: number) => <td key={c}>{cell}</td>)}</tr>)}</tbody>
              </table>
            </div>
          );
        }
        if (block.type === "checkpoint" && typeof block.prompt === "string") {
          return (
            <div className="checkpoint tutor-checkpoint" key={index}>
              <strong>Checkpoint</strong>
              <p>{block.prompt}</p>
            </div>
          );
        }
        return null;
      })}
    </div>
  );
}
