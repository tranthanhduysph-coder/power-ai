export type Language = "vi" | "en";

export type TutorBlock =
  | { type: "text"; content: string }
  | {
      type: "diagram";
      title: string;
      nodes: { id: string; label: string }[];
      edges: { from: string; to: string }[];
    }
  | { type: "table"; headers: string[]; rows: string[][] }
  | { type: "checkpoint"; prompt: string };

export type PracticeQuestion = {
  id: string;
  code: string;
  question_type: "mcq" | "true_false" | "short_answer";
  difficulty: "easy" | "medium" | "hard";
  cognitive_level: string;
  stem_vi: string;
  stem_en: string;
  options: { key: string; text_vi: string; text_en: string }[];
};
