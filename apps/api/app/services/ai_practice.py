from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings


_ALLOWED_TYPES = {"mcq", "true_false", "short_answer"}
_ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}
_ALLOWED_COGNITIVE_LEVELS = {"remember", "understand", "apply", "high_apply"}


def _source_context(db: Session, unit_id) -> tuple[str, str]:
    rows = db.execute(
        text(
            """
            SELECT s.code AS source_code, s.title AS source_title,
                   ch.page_start, ch.page_end, ch.text_content,
                   cus.source_role
            FROM curriculum_unit_sources cus
            JOIN sources s ON s.id = cus.source_id
            JOIN content_chunks ch ON ch.source_id = cus.source_id
            WHERE cus.curriculum_unit_id = :unit_id
              AND (cus.pdf_page_start IS NULL OR ch.page_end IS NULL OR ch.page_end >= cus.pdf_page_start)
              AND (cus.pdf_page_end IS NULL OR ch.page_start IS NULL OR ch.page_start <= cus.pdf_page_end)
            ORDER BY CASE cus.source_role WHEN 'primary' THEN 0 WHEN 'reference' THEN 1 ELSE 2 END,
                     ch.page_start NULLS LAST, ch.chunk_index NULLS LAST
            LIMIT 18
            """
        ),
        {"unit_id": unit_id},
    ).mappings().all()

    if not rows:
        rows = db.execute(
            text(
                """
                SELECT DISTINCT s.code AS source_code, s.title AS source_title,
                       ch.page_start, ch.page_end, ch.text_content,
                       'concept' AS source_role
                FROM curriculum_concepts uc
                JOIN content_chunk_concepts ccc ON ccc.concept_id = uc.concept_id
                JOIN content_chunks ch ON ch.id = ccc.chunk_id
                JOIN sources s ON s.id = ch.source_id
                WHERE uc.curriculum_unit_id = :unit_id
                ORDER BY ch.page_start NULLS LAST
                LIMIT 18
                """
            ),
            {"unit_id": unit_id},
        ).mappings().all()

    context_parts: list[str] = []
    basis_parts: list[str] = []
    total_chars = 0
    for row in rows:
        text_content = (row["text_content"] or "").strip()
        if not text_content:
            continue
        remaining = 18000 - total_chars
        if remaining <= 0:
            break
        text_content = text_content[:remaining]
        page = row["page_start"]
        if row["page_end"] and row["page_end"] != row["page_start"]:
            page = f"{row['page_start']}-{row['page_end']}"
        header = f"SOURCE={row['source_code']}; TITLE={row['source_title']}; PDF_PAGE={page or ''}"
        context_parts.append(f"{header}\n{text_content}")
        basis = f"{row['source_code']} PDF {page}" if page else str(row["source_code"])
        if basis not in basis_parts:
            basis_parts.append(basis)
        total_chars += len(text_content)

    return "\n\n---\n\n".join(context_parts), "; ".join(basis_parts[:8])


def generate_ai_practice_items(
    db: Session,
    *,
    unit_id,
    difficulty: str,
    question_types: list[str],
    question_count: int,
    instruction: str | None,
) -> tuple[str, list[dict[str, Any]], str]:
    settings = get_settings()
    if settings.ai_provider != "openai":
        raise RuntimeError("AI-generated practice requires AI_PROVIDER=openai")
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for AI-generated practice")

    unit = db.execute(
        text(
            """
            SELECT cu.code, cu.name_vi, cu.name_en, g.level AS grade
            FROM curriculum_units cu
            JOIN grades g ON g.id = cu.grade_id
            WHERE cu.id = :unit_id
            """
        ),
        {"unit_id": unit_id},
    ).mappings().one()

    concepts = db.execute(
        text(
            """
            SELECT c.id, c.code, c.name_vi, c.name_en, cc.is_core
            FROM curriculum_concepts cc
            JOIN concepts c ON c.id = cc.concept_id
            WHERE cc.curriculum_unit_id = :unit_id
            ORDER BY cc.is_core DESC, c.code
            """
        ),
        {"unit_id": unit_id},
    ).mappings().all()
    if not concepts:
        raise ValueError("This unit has no mapped concepts for AI practice")

    source_context, source_basis = _source_context(db, unit_id)
    if not source_context:
        raise ValueError("No grounded source context is available for this unit")

    allowed_types = [qtype for qtype in question_types if qtype in _ALLOWED_TYPES]
    if not allowed_types:
        raise ValueError("At least one supported question type is required")

    concept_codes = [str(row["code"]) for row in concepts]
    concept_lines = "\n".join(
        f"- {row['code']}: {row['name_vi']} / {row['name_en']}" for row in concepts
    )
    requested_difficulty = difficulty if difficulty in _ALLOWED_DIFFICULTIES else "mixed"
    user_instruction = (instruction or "").strip()

    schema = {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "minItems": question_count,
                "maxItems": question_count,
                "items": {
                    "type": "object",
                    "properties": {
                        "question_type": {"type": "string", "enum": allowed_types},
                        "difficulty": {"type": "string", "enum": sorted(_ALLOWED_DIFFICULTIES)},
                        "cognitive_level": {"type": "string", "enum": sorted(_ALLOWED_COGNITIVE_LEVELS)},
                        "concept_code": {"type": "string", "enum": concept_codes},
                        "stem_vi": {"type": "string"},
                        "stem_en": {"type": "string"},
                        "answer": {"type": "string"},
                        "explanation_vi": {"type": "string"},
                        "explanation_en": {"type": "string"},
                        "options": {
                            "type": "array",
                            "maxItems": 4,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "key": {"type": "string"},
                                    "text_vi": {"type": "string"},
                                    "text_en": {"type": "string"},
                                },
                                "required": ["key", "text_vi", "text_en"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": [
                        "question_type",
                        "difficulty",
                        "cognitive_level",
                        "concept_code",
                        "stem_vi",
                        "stem_en",
                        "answer",
                        "explanation_vi",
                        "explanation_en",
                        "options",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["questions"],
        "additionalProperties": False,
    }

    instruction_text = f"""
You create a temporary learner practice set for POWER-AI-WEB Biology.
Use ONLY the supplied source context. Do not introduce facts that are not supported by it.
Create exactly {question_count} questions for Biology {unit['grade']}: {unit['name_vi']} / {unit['name_en']}.
Allowed concept codes are listed below; every question must use exactly one of them.
Allowed question types: {', '.join(allowed_types)}.
Requested difficulty: {requested_difficulty}. If it is 'mixed', create a sensible mix of easy, medium, and hard.
Learner request: {user_instruction or '(no additional request)'}.

Rules:
- MCQ: exactly four options A-D, exactly one correct answer; answer must be the option key.
- True/False: options must be an empty array; answer must be exactly 'true' or 'false'.
- Short answer: options must be an empty array; require a short exact-match term, number, symbol, or very short phrase. Do not ask for free-form explanations.
- Write both Vietnamese and English stems and explanations.
- Avoid trick wording, ambiguity, duplicated questions, and answer leakage in the stem.
- These are practice-only AI items, not validated Evaluate-bank items.

CONCEPTS:
{concept_lines}

SOURCE CONTEXT:
{source_context}
""".strip()

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.content_model,
        input=[{"role": "user", "content": instruction_text}],
        text={
            "format": {
                "type": "json_schema",
                "name": "power_ai_practice_set",
                "strict": True,
                "schema": schema,
            }
        },
    )
    raw = (response.output_text or "").strip()
    if not raw:
        raise RuntimeError("OpenAI returned an empty AI practice set")
    payload = json.loads(raw)
    generated = payload.get("questions") or []
    if len(generated) != question_count:
        raise RuntimeError("OpenAI did not return the requested number of questions")

    concept_by_code = {str(row["code"]): row for row in concepts}
    normalized: list[dict[str, Any]] = []
    seen_stems: set[str] = set()
    for item in generated:
        qtype = str(item.get("question_type", "")).strip()
        qdifficulty = str(item.get("difficulty", "")).strip()
        cognitive = str(item.get("cognitive_level", "")).strip()
        concept_code = str(item.get("concept_code", "")).strip()
        stem_vi = str(item.get("stem_vi", "")).strip()
        stem_en = str(item.get("stem_en", "")).strip()
        answer = str(item.get("answer", "")).strip()
        options = item.get("options") or []

        if qtype not in allowed_types:
            raise RuntimeError(f"Unsupported AI question type: {qtype}")
        if qdifficulty not in _ALLOWED_DIFFICULTIES:
            raise RuntimeError(f"Unsupported AI difficulty: {qdifficulty}")
        if cognitive not in _ALLOWED_COGNITIVE_LEVELS:
            raise RuntimeError(f"Unsupported AI cognitive level: {cognitive}")
        if concept_code not in concept_by_code:
            raise RuntimeError(f"AI question used an out-of-unit concept: {concept_code}")
        if not stem_vi or not stem_en or stem_vi.casefold() in seen_stems:
            raise RuntimeError("AI practice contained an empty or duplicate question")
        seen_stems.add(stem_vi.casefold())

        if qtype == "mcq":
            if len(options) != 4:
                raise RuntimeError("AI MCQ must contain exactly four options")
            keys = [str(opt.get("key", "")).strip().upper() for opt in options]
            if keys != ["A", "B", "C", "D"]:
                raise RuntimeError("AI MCQ option keys must be A, B, C, D")
            answer = answer.upper()
            if answer not in keys:
                raise RuntimeError("AI MCQ answer does not match an option key")
            answer_json: Any = {"option": answer}
            normalized_options = [
                {
                    "key": str(opt["key"]).strip().upper(),
                    "text_vi": str(opt["text_vi"]).strip(),
                    "text_en": str(opt["text_en"]).strip(),
                }
                for opt in options
            ]
        elif qtype == "true_false":
            truth = answer.casefold()
            if truth not in {"true", "false"}:
                raise RuntimeError("AI True/False answer must be true or false")
            answer_json = {"value": truth == "true"}
            normalized_options = []
        else:
            if not answer or len(answer) > 120:
                raise RuntimeError("AI short answer must be a short exact-match answer")
            answer_json = {"value": answer}
            normalized_options = []

        concept = concept_by_code[concept_code]
        normalized.append(
            {
                "id": str(uuid4()),
                "code": f"AI_TEMP_{uuid4().hex[:16].upper()}",
                "question_type": qtype,
                "difficulty": qdifficulty,
                "cognitive_level": cognitive,
                "concept_id": str(concept["id"]),
                "concept_code": concept_code,
                "concept_name_vi": concept["name_vi"],
                "concept_name_en": concept["name_en"],
                "stem_vi": stem_vi,
                "stem_en": stem_en,
                "answer_json": answer_json,
                "explanation_vi": str(item.get("explanation_vi", "")).strip(),
                "explanation_en": str(item.get("explanation_en", "")).strip(),
                "options": normalized_options,
            }
        )

    return settings.content_model, normalized, source_basis or "source-grounded unit context"
