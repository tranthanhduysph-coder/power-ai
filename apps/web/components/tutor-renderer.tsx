"use client";

import type { TutorBlock } from "@/lib/types";

export function TutorRenderer({ blocks }: { blocks: TutorBlock[] }) {
  return (
    <div className="tutor-blocks">
      {blocks.map((block, index) => {
        if (block.type === "text") return <p key={index} className="tutor-text">{block.content}</p>;
        if (block.type === "table") {
          return (
            <div className="table-scroll" key={index}>
              <table>
                <thead><tr>{block.headers.map((h) => <th key={h}>{h}</th>)}</tr></thead>
                <tbody>{block.rows.map((row, r) => <tr key={r}>{row.map((cell, c) => <td key={c}>{cell}</td>)}</tr>)}</tbody>
              </table>
            </div>
          );
        }
        if (block.type === "diagram") {
          return (
            <div className="diagram" key={index}>
              <strong>{block.title}</strong>
              <div className="diagram-row">
                {block.nodes.map((node, i) => (
                  <div key={node.id} className="diagram-node">
                    {node.label}
                    {i < block.nodes.length - 1 && <span className="diagram-arrow">→</span>}
                  </div>
                ))}
              </div>
            </div>
          );
        }
        return <div key={index} className="checkpoint">✓ {block.prompt}</div>;
      })}
    </div>
  );
}
