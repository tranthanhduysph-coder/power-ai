from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings

_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", flags=re.IGNORECASE | re.DOTALL)
_CODE_RE = re.compile(r"^[A-Z0-9_.-]{3,120}$")
_ALLOWED_RELATIONS = {"prerequisite", "related", "part_of", "contrasts_with", "applied_in"}
_ALLOWED_QTYPES = {"mcq", "true_false", "short_answer"}
_ALLOWED_DIFFICULTY = {"easy", "medium", "hard"}
_ALLOWED_COGNITIVE = {"remember", "understand", "apply", "high_apply"}

# V159_CANONICAL_PRIMARY_LOCK: preserve curriculum primary across regeneration/replacement.


@dataclass(frozen=True)
class UnitSourceContext:
    unit: dict[str, Any]
    source_code: str
    source_title: str
    pdf_page_start: int
    pdf_page_end: int
    text: str
    fingerprint: str
    primary_concept_code: str | None = None




def _coerce_bool(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "đúng", "dung", "yes", "y", "1"}:
            return True
        if normalized in {"false", "sai", "no", "n", "0"}:
            return False
    return value


def _normalize_concept_code(value: Any) -> Any:
    """Canonicalize harmless separator drift in BIO concept identifiers.

    The content model sometimes emits BIO_GENE or BIO-RNA-TYPES even though
    POWER's ontology uses dotted identifiers such as BIO.GENE and BIO.RNA.TYPES.
    Only BIO-prefixed values are normalized; unrelated/invalid identifiers stay
    untouched so strict validation can still reject them.
    """
    if not isinstance(value, str):
        return value
    raw = value.strip().upper()
    if not raw:
        return raw
    if raw == "BIO":
        return raw
    if raw.startswith("BIO_") or raw.startswith("BIO-") or raw.startswith("BIO "):
        raw = "BIO." + raw[4:]
    elif raw.startswith("BIO."):
        pass
    else:
        return raw
    raw = re.sub(r"[\s_-]+", ".", raw)
    raw = re.sub(r"\.+", ".", raw).strip(".")
    return raw


def _match_tokens(value: Any) -> set[str]:
    text_value = str(value or "").lower()
    text_value = re.sub(r"[^0-9a-zà-ỹđ]+", " ", text_value, flags=re.IGNORECASE)
    stop = {
        "va", "và", "cua", "của", "la", "là", "cho", "trong", "voi", "với",
        "the", "of", "and", "in", "to", "a", "an", "biology", "sinh", "hoc", "học",
    }
    return {token for token in text_value.split() if len(token) >= 3 and token not in stop}


def _repair_primary_question_mapping(payload: dict[str, Any]) -> None:
    """Repair only clearly mis-tagged Evaluate coverage of the primary concept.

    The model occasionally writes a question whose stem explicitly names the primary
    concept but assigns a neighbouring concept_code. In that narrow case we can
    safely repair the metadata without rewriting the question. If no question
    clearly refers to the primary concept, leave the draft unchanged so QA can
    reject it and require regeneration rather than inventing an assessment item.
    """
    policy = payload.get("policy") or {}
    primary = str(policy.get("primary_concept_code") or "")
    if not primary:
        return
    questions = [q for q in (payload.get("questions") or []) if isinstance(q, dict)]
    if any(str(q.get("concept_code") or "") == primary for q in questions):
        return

    primary_concept = next(
        (c for c in (payload.get("concepts") or []) if isinstance(c, dict) and str(c.get("code") or "") == primary),
        None,
    )
    if not primary_concept:
        return

    alias_tokens = _match_tokens(primary_concept.get("name_vi")) | _match_tokens(primary_concept.get("name_en"))
    # Code fragments are useful only as a fallback for compact terms such as DNA/RNA.
    alias_tokens |= {part.lower() for part in primary.split(".")[1:] if len(part) >= 3}
    if not alias_tokens:
        return

    best_question: dict[str, Any] | None = None
    best_score = 0
    for question in questions:
        stem_tokens = _match_tokens(question.get("stem_vi")) | _match_tokens(question.get("stem_en"))
        overlap = alias_tokens & stem_tokens
        # Require at least two meaningful shared terms, or one distinctive long token.
        score = len(overlap)
        distinctive = any(len(token) >= 7 for token in overlap)
        if score >= 2 or distinctive:
            if score > best_score or best_question is None:
                best_question = question
                best_score = score

    if best_question is not None:
        best_question["concept_code"] = primary


def normalize_power_draft_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize harmless model JSON type drift before strict validation/storage.

    The validator remains strict; this only converts unambiguous boolean-like
    values that models sometimes emit as strings or 0/1.
    """
    normalized = copy.deepcopy(payload)

    # Canonicalize concept identifiers and every reference to them before
    # strict validation. This lets harmless model separator drift (BIO_GENE)
    # become the POWER ontology form (BIO.GENE) without weakening validation.
    for concept in normalized.get("concepts") or []:
        if isinstance(concept, dict) and "code" in concept:
            concept["code"] = _normalize_concept_code(concept.get("code"))

    concept_code_set = {
        str(concept.get("code"))
        for concept in (normalized.get("concepts") or [])
        if isinstance(concept, dict) and concept.get("code")
    }

    # Relations are generated scaffolding, so repair only unambiguous structural
    # defects before strict validation: normalize concept codes, drop self-links,
    # drop links to concepts that are not in this draft, and remove duplicates.
    # Unsupported relation types are intentionally preserved so validation can
    # still reject them instead of silently changing their meaning.
    repaired_relations: list[Any] = []
    seen_relations: set[tuple[str, str, str]] = set()
    for relation in normalized.get("relations") or []:
        if not isinstance(relation, dict):
            repaired_relations.append(relation)
            continue
        relation["source_code"] = _normalize_concept_code(relation.get("source_code"))
        relation["target_code"] = _normalize_concept_code(relation.get("target_code"))
        source = str(relation.get("source_code") or "")
        target = str(relation.get("target_code") or "")
        relation_type = str(relation.get("relation_type") or "")
        if source == target:
            continue
        if source not in concept_code_set or target not in concept_code_set:
            continue
        key = (source, target, relation_type)
        if key in seen_relations:
            continue
        seen_relations.add(key)
        repaired_relations.append(relation)
    normalized["relations"] = repaired_relations

    prepare = normalized.get("prepare") or {}
    for item in prepare.get("diagnostic_items") or []:
        if isinstance(item, dict):
            item["concept_code"] = _normalize_concept_code(item.get("concept_code"))

    work = normalized.get("work") or {}
    for lang in ("vi", "en"):
        for task in ((work.get(lang) or {}).get("tasks") or []):
            if isinstance(task, dict):
                task["concept_codes"] = [
                    _normalize_concept_code(code) for code in (task.get("concept_codes") or [])
                ]

    policy = normalized.get("policy") or {}
    if isinstance(policy, dict):
        policy["primary_concept_code"] = _normalize_concept_code(policy.get("primary_concept_code"))

    for question in normalized.get("questions") or []:
        if isinstance(question, dict):
            question["concept_code"] = _normalize_concept_code(question.get("concept_code"))

    prepare = normalized.get("prepare") or {}
    for item in prepare.get("diagnostic_items") or []:
        if isinstance(item, dict) and item.get("question_type") == "true_false":
            item["expected"] = _coerce_bool(item.get("expected"))
            item["options"] = []

    for question in normalized.get("questions") or []:
        if not isinstance(question, dict):
            continue
        if question.get("question_type") == "true_false":
            answer = question.get("answer_json")
            if isinstance(answer, dict):
                answer["value"] = _coerce_bool(answer.get("value"))
            question["options"] = []
        for option in question.get("options") or []:
            if isinstance(option, dict) and "is_correct" in option:
                option["is_correct"] = _coerce_bool(option.get("is_correct"))


        # V158_MCQ_NORMALIZE_FROM_ANSWER
        # answer_json is the canonical answer. If the LLM omitted/garbled
        # options[].is_correct, derive the flags deterministically when exactly
        # one of the four option keys matches answer_json.option.
        if isinstance(question, dict):
            _v158_qtype = str(
                question.get("question_type")
                or question.get("type")
                or ""
            ).strip().lower()
            if _v158_qtype == "mcq":
                _v158_options = question.get("options") or []
                _v158_answer = question.get("answer_json") or {}
                _v158_answer_key = (
                    _v158_answer.get("option")
                    if isinstance(_v158_answer, dict)
                    else None
                )
                if len(_v158_options) == 4 and _v158_answer_key is not None:
                    _v158_answer_key_norm = str(_v158_answer_key).strip().upper()
                    _v158_matches = [
                        idx
                        for idx, opt in enumerate(_v158_options)
                        if isinstance(opt, dict)
                        and str(opt.get("key") or "").strip().upper()
                        == _v158_answer_key_norm
                    ]
                    _v158_explicit_true = [
                        idx
                        for idx, opt in enumerate(_v158_options)
                        if isinstance(opt, dict)
                        and opt.get("is_correct") is True
                    ]
                    if len(_v158_explicit_true) != 1 and len(_v158_matches) == 1:
                        _v158_correct_idx = _v158_matches[0]
                        for idx, opt in enumerate(_v158_options):
                            if isinstance(opt, dict):
                                opt["is_correct"] = idx == _v158_correct_idx
                        # Canonicalize answer key casing to the actual option key
                        # so the existing validator's strict equality also passes.
                        if isinstance(_v158_answer, dict):
                            _v158_answer["option"] = str(
                                _v158_options[_v158_correct_idx].get("key")
                            )
    for concept in normalized.get("concepts") or []:
        if isinstance(concept, dict) and "is_core" in concept:
            concept["is_core"] = _coerce_bool(concept.get("is_core"))

    # Repair harmless model drift in the number of core concepts. POWER requires
    # 3–6 core concepts for a unit. The exact core flag is scaffolding metadata,
    # so we can repair it deterministically without changing the concept set:
    # always keep the primary concept core, promote concepts in source order until
    # there are at least 3, and trim excess core flags to at most 6.
    concepts = [c for c in (normalized.get("concepts") or []) if isinstance(c, dict)]
    policy = normalized.get("policy") or {}
    primary = policy.get("primary_concept_code") if isinstance(policy, dict) else None
    if concepts:
        by_code = {str(c.get("code") or ""): c for c in concepts if c.get("code")}
        if primary in by_code:
            by_code[str(primary)]["is_core"] = True

        core = [c for c in concepts if c.get("is_core") is True]
        if len(core) < 3:
            for concept in concepts:
                if concept.get("is_core") is not True:
                    concept["is_core"] = True
                    core.append(concept)
                    if len(core) >= 3:
                        break

        core = [c for c in concepts if c.get("is_core") is True]
        if len(core) > 6:
            keep_codes: list[str] = []
            if primary in by_code:
                keep_codes.append(str(primary))
            for concept in concepts:
                code = str(concept.get("code") or "")
                if concept.get("is_core") is True and code not in keep_codes:
                    keep_codes.append(code)
                if len(keep_codes) >= 6:
                    break
            keep = set(keep_codes[:6])
            for concept in concepts:
                concept["is_core"] = str(concept.get("code") or "") in keep

    # Ensure Evaluate metadata covers the primary concept when a generated question
    # already clearly asks about it. This removes harmless tagging drift while
    # refusing to fabricate a new question when primary coverage is genuinely absent.
    _repair_primary_question_mapping(normalized)

    return normalized


def _extract_json_object(raw: str) -> dict[str, Any]:
    cleaned = _JSON_FENCE.sub("", raw.strip()).strip()
    try:
        value = json.loads(cleaned)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        value = json.loads(cleaned[start : end + 1])
        if isinstance(value, dict):
            return value
    raise ValueError("POWER content model did not return a valid JSON object")


def load_unit_source_context(db: Session, unit_code: str, *, max_chars: int = 36000) -> UnitSourceContext:
    unit = db.execute(
        text(
            """
            SELECT cu.id::text AS id, cu.code, cu.name_vi, cu.name_en, cu.unit_type,
                   cu.lesson_number, cu.printed_page_start, cu.printed_page_end,
                   cu.content_status, cu.is_power_ready, cu.power_status,
                   cu.metadata_json->>'primary_concept_code' AS primary_concept_code,
                   g.level AS grade,
                   s.code AS source_code, s.title AS source_title,
                   cus.pdf_page_start, cus.pdf_page_end
            FROM curriculum_units cu
            JOIN grades g ON g.id=cu.grade_id
            JOIN curriculum_unit_sources cus ON cus.curriculum_unit_id=cu.id AND cus.source_role='primary'
            JOIN sources s ON s.id=cus.source_id
            WHERE cu.code=:unit_code AND cu.catalog_visible=true
            ORDER BY s.code
            LIMIT 1
            """
        ),
        {"unit_code": unit_code},
    ).mappings().one_or_none()
    if not unit:
        raise KeyError(unit_code)
    if unit["content_status"] != "ingested":
        raise ValueError(f"{unit_code} is not ingested yet")
    if unit["pdf_page_start"] is None or unit["pdf_page_end"] is None:
        raise ValueError(f"{unit_code} has no verified PDF page mapping")

    chunks = db.execute(
        text(
            """
            SELECT cc.page_start, cc.page_end, cc.chunk_index, cc.text_content
            FROM content_chunks cc
            JOIN sources s ON s.id=cc.source_id
            WHERE s.code=:source_code
              AND cc.page_start IS NOT NULL AND cc.page_end IS NOT NULL
              AND cc.page_end >= :pdf_start
              AND cc.page_start <= :pdf_end
            ORDER BY cc.page_start, cc.chunk_index NULLS LAST, cc.created_at
            """
        ),
        {
            "source_code": unit["source_code"],
            "pdf_start": unit["pdf_page_start"],
            "pdf_end": unit["pdf_page_end"],
        },
    ).mappings().all()
    if not chunks:
        raise ValueError(f"No source chunks overlap {unit_code}")

    parts: list[str] = []
    used = 0
    for row in chunks:
        label = f"[PDF {row['page_start']}-{row['page_end']}]\n"
        body = str(row["text_content"] or "").strip()
        piece = label + body
        if used + len(piece) > max_chars:
            remaining = max_chars - used
            if remaining > 500:
                parts.append(piece[:remaining])
            break
        parts.append(piece)
        used += len(piece)
    source_text = "\n\n---\n\n".join(parts).strip()
    fingerprint = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    return UnitSourceContext(
        unit=dict(unit),
        source_code=str(unit["source_code"]),
        source_title=str(unit["source_title"]),
        pdf_page_start=int(unit["pdf_page_start"]),
        pdf_page_end=int(unit["pdf_page_end"]),
        text=source_text,
        fingerprint=fingerprint,
        primary_concept_code=(
            str(_normalize_concept_code(unit.get("primary_concept_code")))
            if unit.get("primary_concept_code")
            else None
        ),
    )


def build_generation_prompt(context: UnitSourceContext) -> str:
    u = context.unit
    return f"""
You are building ONE source-grounded POWER Biology learning unit.
POWER means Prepare → Organize → Work → Evaluate → Rethink.
The learner, not the AI, must own the learning work. AI scaffolds, asks focused questions, and gives feedback.

STRICT SOURCE RULES
- Use ONLY the supplied Vietnamese textbook context below.
- Preserve the textbook's terminology and scope.
- Do not add outside facts, modernize claims, or invent learning outcomes unsupported by the source.
- If the source is insufficient for an item, make the item simpler instead of inventing content.
- Return VALID JSON ONLY. No Markdown fences and no commentary.

UNIT
code: {u['code']}
grade: {u['grade']}
type: {u['unit_type']}
Vietnamese title: {u['name_vi']}
English title: {u['name_en']}
printed pages: {u['printed_page_start']}-{u['printed_page_end']}
source: {context.source_code}
PDF pages: {context.pdf_page_start}-{context.pdf_page_end}
canonical primary concept: {context.primary_concept_code or "NOT YET SET"}

Return this exact top-level shape:
{{
  "schema_version": "1.2",
  "concepts": [
    {{"code":"BIO....","name_vi":"...","name_en":"...","description_vi":"...","description_en":"...","is_core":true}}
  ],
  "relations": [
    {{"source_code":"BIO....","target_code":"BIO....","relation_type":"prerequisite|related|part_of|contrasts_with|applied_in"}}
  ],
  "prepare": {{
    "title_vi":"...","title_en":"...",
    "outcomes_vi":["..."],"outcomes_en":["..."],
    "keywords":["..."],
    "diagnostic_items":[
      {{"code":"PREP_...","concept_code":"BIO....","question_type":"mcq|true_false","prompt_vi":"...","prompt_en":"...","options":[{{"key":"A","text_vi":"...","text_en":"..."}}],"expected":"A"}}
    ]
  }},
  "work": {{
    "vi": {{"title":"...","intro":"...","tasks":[{{"code":"W1_...","title":"...","prompt":"...","concept_codes":["BIO...."],"minimum_chars":80,"scaffold":["...","..."]}}],"self_check_prompt":"..."}},
    "en": {{"title":"...","intro":"...","tasks":[{{"code":"W1_...","title":"...","prompt":"...","concept_codes":["BIO...."],"minimum_chars":80,"scaffold":["...","..."]}}],"self_check_prompt":"..."}}
  }},
  "policy": {{"primary_concept_code":"BIO....","minimum_anchor_concepts":3,"minimum_links":3}},
  "questions": [
    {{
      "question_type":"mcq|true_false|short_answer","difficulty":"easy|medium|hard","cognitive_level":"remember|understand|apply|high_apply",
      "stem_vi":"...","stem_en":"...","answer_json":{{"option":"A"}},
      "explanation_vi":"...","explanation_en":"...","concept_code":"BIO....",
      "options":[{{"key":"A","text_vi":"...","text_en":"...","is_correct":true}}]
    }}
  ]
}}

QUALITY REQUIREMENTS
- If "canonical primary concept" above is not "NOT YET SET", policy.primary_concept_code MUST equal that exact code; the same exact code MUST appear in concepts with is_core=true; and at least one Evaluate question MUST use that exact concept_code. Never replace an existing canonical primary with a newly invented alternative code.
- concepts: 4–8 concepts; 3–6 should be core. Codes must use canonical dotted identifiers: BIO.<DOMAIN>.<CONCEPT> (for example BIO.GENE.EXPRESSION). Never use BIO_GENE, BIO-GENE, spaces, or other separators.
- relations: 2–8 meaningful relationships among returned concepts. Every source_code and target_code must exactly match a code returned in concepts, and source_code must never equal target_code.
- Prepare: 2–4 measurable outcomes and exactly 3 prerequisite/diagnostic items. Diagnostic items test prerequisite/readiness, not the whole lesson.
- Diagnostic MCQ uses expected as an option key string such as "A". Diagnostic true_false MUST use JSON boolean expected: true or false (never "true", "false", "Đúng", or "Sai") and options=[].
- Work: exactly 3 learner-owned tasks in both languages with matching task codes. Tasks should require explanation, comparison, analysis, interpretation, or application as supported by the source; never simply ask the learner to copy text.
- Questions: 8–10 source-grounded items, at least 3 MCQ and 3 true/false. Add short_answer only when a short canonical answer is genuinely unambiguous. MCQ has exactly 4 options with one correct option. true_false uses answer_json {{"value":true/false}} and options=[]. short_answer uses answer_json {{"value":"..."}} and options=[].
- Evaluate MUST directly assess policy.primary_concept_code in at least one question: at least one questions[].concept_code must exactly equal policy.primary_concept_code, and that question stem must genuinely assess that concept.
- Difficulty should be mixed. Avoid trick wording.
- Vietnamese wording is primary; English is a faithful learning translation, not an expansion.

TEXTBOOK CONTEXT
{context.text}
""".strip()


def generate_power_draft(context: UnitSourceContext) -> tuple[str, dict[str, Any]]:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required to generate POWER drafts")
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.content_model,
        input=[{"role": "user", "content": build_generation_prompt(context)}],
    )
    payload = normalize_power_draft_payload(_extract_json_object(response.output_text))
    return settings.content_model, payload


def validate_power_draft(payload: dict[str, Any]) -> dict[str, Any]:
    payload = normalize_power_draft_payload(payload)
    errors: list[str] = []
    warnings: list[str] = []

    concepts = payload.get("concepts") or []
    if not isinstance(concepts, list) or not 4 <= len(concepts) <= 8:
        errors.append("concepts must contain 4–8 items")
        concepts = concepts if isinstance(concepts, list) else []
    codes: list[str] = []
    core_count = 0
    for i, concept in enumerate(concepts):
        if not isinstance(concept, dict):
            errors.append(f"concepts[{i}] must be an object")
            continue
        code = str(concept.get("code") or "").strip()
        if not code.startswith("BIO.") or not _CODE_RE.match(code):
            errors.append(f"invalid concept code: {code}")
        if code in codes:
            errors.append(f"duplicate concept code: {code}")
        codes.append(code)
        if concept.get("is_core") is True:
            core_count += 1
        for key in ("name_vi", "name_en", "description_vi", "description_en"):
            if not str(concept.get(key) or "").strip():
                errors.append(f"{code or i} missing {key}")
    if concepts and not 3 <= core_count <= 6:
        errors.append("3–6 concepts must be marked core")
    code_set = set(codes)

    for i, rel in enumerate(payload.get("relations") or []):
        if not isinstance(rel, dict):
            errors.append(f"relations[{i}] must be an object")
            continue
        if rel.get("source_code") not in code_set or rel.get("target_code") not in code_set:
            errors.append(f"relations[{i}] references unknown concept")
        if rel.get("source_code") == rel.get("target_code"):
            errors.append(f"relations[{i}] links a concept to itself")
        if rel.get("relation_type") not in _ALLOWED_RELATIONS:
            errors.append(f"relations[{i}] has unsupported relation_type")

    prepare = payload.get("prepare") or {}
    for key in ("title_vi", "title_en"):
        if not str(prepare.get(key) or "").strip():
            errors.append(f"prepare missing {key}")
    for key in ("outcomes_vi", "outcomes_en"):
        values = prepare.get(key) or []
        if not isinstance(values, list) or not 2 <= len(values) <= 4:
            errors.append(f"prepare.{key} must contain 2–4 outcomes")
    diagnostics = prepare.get("diagnostic_items") or []
    if not isinstance(diagnostics, list) or len(diagnostics) != 3:
        errors.append("prepare.diagnostic_items must contain exactly 3 items")
        diagnostics = diagnostics if isinstance(diagnostics, list) else []
    seen_diag: set[str] = set()
    for i, item in enumerate(diagnostics):
        if not isinstance(item, dict):
            errors.append(f"diagnostic_items[{i}] must be an object")
            continue
        code = str(item.get("code") or "")
        if not code or code in seen_diag:
            errors.append(f"diagnostic_items[{i}] needs a unique code")
        seen_diag.add(code)
        if item.get("concept_code") not in code_set:
            errors.append(f"diagnostic_items[{i}] references unknown concept")
        qtype = item.get("question_type")
        if qtype not in {"mcq", "true_false"}:
            errors.append(f"diagnostic_items[{i}] has invalid question_type")
        if qtype == "mcq":
            options = item.get("options") or []
            keys = [str(o.get("key")) for o in options if isinstance(o, dict)]
            if len(options) != 4 or item.get("expected") not in keys:
                errors.append(f"diagnostic_items[{i}] MCQ must have 4 options and valid expected key")
        elif qtype == "true_false" and not isinstance(item.get("expected"), bool):
            errors.append(f"diagnostic_items[{i}] true_false expected must be boolean")

    work = payload.get("work") or {}
    for lang in ("vi", "en"):
        raw = work.get(lang) or {}
        tasks = raw.get("tasks") or []
        if len(tasks) != 3:
            errors.append(f"work.{lang}.tasks must contain exactly 3 tasks")
            continue
        for i, task in enumerate(tasks):
            if not str(task.get("code") or "").strip():
                errors.append(f"work.{lang}.tasks[{i}] missing code")
            refs = task.get("concept_codes") or []
            if not refs or any(code not in code_set for code in refs):
                errors.append(f"work.{lang}.tasks[{i}] has invalid concept_codes")
            if int(task.get("minimum_chars") or 0) < 60:
                errors.append(f"work.{lang}.tasks[{i}] minimum_chars must be >= 60")
            if len(task.get("scaffold") or []) < 2:
                errors.append(f"work.{lang}.tasks[{i}] needs at least 2 scaffold prompts")
    vi_codes = [x.get("code") for x in ((work.get("vi") or {}).get("tasks") or [])]
    en_codes = [x.get("code") for x in ((work.get("en") or {}).get("tasks") or [])]
    if vi_codes and en_codes and vi_codes != en_codes:
        errors.append("Vietnamese and English Work task codes must match")

    policy = payload.get("policy") or {}
    primary = policy.get("primary_concept_code")
    if primary not in code_set:
        errors.append("policy.primary_concept_code must reference a returned concept")
    if int(policy.get("minimum_anchor_concepts") or 0) < 2:
        errors.append("minimum_anchor_concepts must be >= 2")
    if int(policy.get("minimum_links") or 0) < 2:
        errors.append("minimum_links must be >= 2")

    questions = payload.get("questions") or []
    if not isinstance(questions, list) or not 8 <= len(questions) <= 10:
        errors.append("questions must contain 8–10 items")
        questions = questions if isinstance(questions, list) else []
    mcq_count = tf_count = 0
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            errors.append(f"questions[{i}] must be an object")
            continue
        qtype = q.get("question_type")
        if qtype not in _ALLOWED_QTYPES:
            errors.append(f"questions[{i}] invalid question_type")
            continue
        if qtype == "mcq":
            mcq_count += 1
        elif qtype == "true_false":
            tf_count += 1
        if q.get("difficulty") not in _ALLOWED_DIFFICULTY:
            errors.append(f"questions[{i}] invalid difficulty")
        if q.get("cognitive_level") not in _ALLOWED_COGNITIVE:
            errors.append(f"questions[{i}] invalid cognitive_level")
        if q.get("concept_code") not in code_set:
            errors.append(f"questions[{i}] references unknown concept")
        for key in ("stem_vi", "stem_en", "explanation_vi", "explanation_en"):
            if not str(q.get(key) or "").strip():
                errors.append(f"questions[{i}] missing {key}")
        answer = q.get("answer_json") or {}
        options = q.get("options") or []
        if qtype == "mcq":
            keys = [str(o.get("key")) for o in options if isinstance(o, dict)]
            correct = [o for o in options if isinstance(o, dict) and o.get("is_correct") is True]
            if len(options) != 4 or len(correct) != 1 or answer.get("option") not in keys:
                errors.append(f"questions[{i}] MCQ must have 4 options, one correct, and matching answer_json")
        elif qtype == "true_false":
            if options:
                errors.append(f"questions[{i}] true_false options must be empty")
            if not isinstance(answer.get("value"), bool):
                errors.append(f"questions[{i}] true_false answer_json.value must be boolean")
        elif qtype == "short_answer":
            if options:
                errors.append(f"questions[{i}] short_answer options must be empty")
            if str(answer.get("value") or "").strip() == "":
                errors.append(f"questions[{i}] short_answer needs canonical answer_json.value")
    if mcq_count < 3:
        errors.append("questions need at least 3 MCQ items")
    if tf_count < 3:
        errors.append("questions need at least 3 true/false items")

    if primary in code_set:
        primary_assessed = any(
            isinstance(q, dict) and q.get("concept_code") == primary
            for q in questions
        )
        if not primary_assessed:
            errors.append(
                "primary concept must be directly assessed by at least one Evaluate question"
            )

    if not payload.get("schema_version"):
        warnings.append("schema_version missing")
    return {"valid": not errors, "errors": errors, "warnings": warnings}



def _norm_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def assess_power_draft(
    payload: dict[str, Any],
    *,
    stored_fingerprint: str | None = None,
    current_fingerprint: str | None = None,
    source_chars: int | None = None,
) -> dict[str, Any]:
    """Run deterministic QA on a generated POWER package.

    This is deliberately stricter than schema validation but does not try to
    replace human pedagogical review. A QA pass means the package is internally
    coherent, current with its source, and safe for batch activation.
    """
    normalized = normalize_power_draft_payload(payload)
    validation = validate_power_draft(normalized)
    errors = list(validation["errors"])
    warnings = list(validation["warnings"])

    if stored_fingerprint and current_fingerprint and stored_fingerprint != current_fingerprint:
        errors.append("source fingerprint changed since draft generation")

    if source_chars is not None and source_chars < 1000:
        warnings.append("source context is short (<1000 chars); manual review recommended")

    questions = normalized.get("questions") or []
    stems_vi = [_norm_text(q.get("stem_vi")) for q in questions if isinstance(q, dict)]
    duplicate_stems = sorted({x for x in stems_vi if x and stems_vi.count(x) > 1})
    if duplicate_stems:
        errors.append(f"duplicate Vietnamese question stems: {len(duplicate_stems)}")

    work_vi = ((normalized.get("work") or {}).get("vi") or {}).get("tasks") or []
    work_prompts = [_norm_text(t.get("prompt")) for t in work_vi if isinstance(t, dict)]
    duplicate_work = sorted({x for x in work_prompts if x and work_prompts.count(x) > 1})
    if duplicate_work:
        errors.append(f"duplicate Work prompts: {len(duplicate_work)}")

    qtypes: dict[str, int] = {}
    difficulties: dict[str, int] = {}
    cognitive: dict[str, int] = {}
    concept_refs: set[str] = set()
    for q in questions:
        if not isinstance(q, dict):
            continue
        for bucket, key in ((qtypes, "question_type"), (difficulties, "difficulty"), (cognitive, "cognitive_level")):
            value = str(q.get(key) or "")
            bucket[value] = bucket.get(value, 0) + 1
        if q.get("concept_code"):
            concept_refs.add(str(q["concept_code"]))

    concepts = normalized.get("concepts") or []
    core_codes = {str(c.get("code")) for c in concepts if isinstance(c, dict) and c.get("is_core") is True}
    primary = str(((normalized.get("policy") or {}).get("primary_concept_code")) or "")
    primary_assessed_count = sum(
        1 for q in questions
        if isinstance(q, dict) and str(q.get("concept_code") or "") == primary
    ) if primary else 0
    if primary and primary_assessed_count == 0:
        errors.append("primary concept must be directly assessed by at least one Evaluate question")
    if len(concept_refs) < min(2, len(core_codes)):
        warnings.append("Evaluate questions cover fewer than 2 concepts")
    if len([k for k, v in difficulties.items() if k and v]) < 2:
        warnings.append("Evaluate questions use only one difficulty level")
    if len([k for k, v in cognitive.items() if k and v]) < 2:
        warnings.append("Evaluate questions use only one cognitive level")

    metrics = {
        "concept_count": len(concepts),
        "core_concept_count": len(core_codes),
        "relation_count": len(normalized.get("relations") or []),
        "question_count": len(questions),
        "question_types": qtypes,
        "difficulty_mix": difficulties,
        "cognitive_mix": cognitive,
        "assessed_concepts": sorted(concept_refs),
        "primary_assessed_count": primary_assessed_count,
        "work_task_count": len(work_vi),
        "source_chars": source_chars,
        "source_fingerprint_current": (not stored_fingerprint or not current_fingerprint or stored_fingerprint == current_fingerprint),
    }
    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
        "normalized_payload": normalized,
    }


def qa_latest_draft(db: Session, unit_code: str) -> dict[str, Any]:
    draft = latest_draft(db, unit_code)
    context = load_unit_source_context(db, unit_code)
    qa = assess_power_draft(
        draft["payload_json"],
        stored_fingerprint=draft.get("source_fingerprint"),
        current_fingerprint=context.fingerprint,
        source_chars=len(context.text),
    )
    validation = validate_power_draft(qa["normalized_payload"])
    qa_status = "passed" if qa["passed"] else "failed"
    draft_status = "validated" if validation["valid"] else "draft"
    db.execute(
        text(
            """
            UPDATE power_blueprint_drafts
            SET payload_json=CAST(:payload AS jsonb),
                validation_json=CAST(:validation AS jsonb),
                status=:draft_status,
                qa_status=:qa_status,
                qa_json=CAST(:qa AS jsonb),
                qa_checked_at=now(), updated_at=now()
            WHERE id=CAST(:id AS uuid)
            """
        ),
        {
            "id": draft["id"],
            "payload": json.dumps(qa["normalized_payload"], ensure_ascii=False),
            "validation": json.dumps(validation, ensure_ascii=False),
            "draft_status": draft_status,
            "qa_status": qa_status,
            "qa": json.dumps({k: v for k, v in qa.items() if k != "normalized_payload"}, ensure_ascii=False),
        },
    )
    if not draft["is_power_ready"]:
        db.execute(
            text("UPDATE curriculum_units SET power_status=:status WHERE code=:code"),
            {"status": draft_status, "code": unit_code},
        )
    return {
        "unit_code": unit_code,
        "draft_version": draft["version"],
        "qa_status": qa_status,
        "passed": qa["passed"],
        "errors": qa["errors"],
        "warnings": qa["warnings"],
        "metrics": qa["metrics"],
    }

def save_draft(db: Session, *, unit_code: str, model: str, payload: dict[str, Any], fingerprint: str) -> dict[str, Any]:
    payload = normalize_power_draft_payload(payload)
    validation = validate_power_draft(payload)

    unit_row = db.execute(
        text(
            """
            SELECT id,
                   metadata_json->>'primary_concept_code' AS primary_concept_code
            FROM curriculum_units
            WHERE code=:code
            """
        ),
        {"code": unit_code},
    ).mappings().one()
    unit_id = unit_row["id"]

    canonical_primary = (
        str(_normalize_concept_code(unit_row.get("primary_concept_code")))
        if unit_row.get("primary_concept_code")
        else None
    )
    generated_primary = str(
        ((payload.get("policy") or {}).get("primary_concept_code")) or ""
    )
    if canonical_primary and generated_primary != canonical_primary:
        validation["errors"].append(
            "policy.primary_concept_code must preserve curriculum canonical primary "
            f"{canonical_primary}; got {generated_primary or '<missing>'}"
        )
        validation["valid"] = False

    version = int(db.execute(
        text("SELECT COALESCE(MAX(version),0)+1 FROM power_blueprint_drafts WHERE curriculum_unit_id=:id"),
        {"id": unit_id},
    ).scalar_one())
    status = "validated" if validation["valid"] else "draft"
    row = db.execute(
        text(
            """
            INSERT INTO power_blueprint_drafts(
                curriculum_unit_id, version, status, payload_json, validation_json,
                source_fingerprint, model
            ) VALUES (
                :unit_id, :version, :status, CAST(:payload AS jsonb), CAST(:validation AS jsonb),
                :fingerprint, :model
            )
            RETURNING id::text AS id, version, status
            """
        ),
        {
            "unit_id": unit_id,
            "version": version,
            "status": status,
            "payload": json.dumps(payload, ensure_ascii=False),
            "validation": json.dumps(validation, ensure_ascii=False),
            "fingerprint": fingerprint,
            "model": model,
        },
    ).mappings().one()
    db.execute(
        text("UPDATE curriculum_units SET power_status=:status WHERE id=:id AND is_power_ready=false"),
        {"status": status, "id": unit_id},
    )
    return {**dict(row), "validation": validation}


def latest_draft(db: Session, unit_code: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT pbd.id::text AS id, pbd.version, pbd.status, pbd.payload_json,
                   pbd.validation_json, pbd.source_fingerprint, pbd.model,
                   pbd.qa_status, pbd.qa_json, pbd.qa_checked_at,
                   cu.id::text AS curriculum_unit_id, cu.content_status, cu.is_power_ready,
                   cu.power_status, cu.name_vi, cu.name_en,
                   cu.metadata_json->>'primary_concept_code' AS canonical_primary_concept_code
            FROM power_blueprint_drafts pbd
            JOIN curriculum_units cu ON cu.id=pbd.curriculum_unit_id
            WHERE cu.code=:unit_code
            ORDER BY pbd.version DESC LIMIT 1
            """
        ),
        {"unit_code": unit_code},
    ).mappings().one_or_none()
    if not row:
        raise KeyError(unit_code)
    return dict(row)


def _safe_question_code(unit_code: str, index: int) -> str:
    base = re.sub(r"[^A-Z0-9_]+", "_", unit_code.upper())
    return f"AUTO_{base}_Q{index:02d}"


def _activation_option_params(question_id, option):
    """Build safe DB params for question_options during activation.

    Some normalized/QA-passed drafts can still have raw MCQ options without
    `is_correct`. Activation must derive correctness from answer_json rather
    than assuming the model persisted that boolean on every option.
    """
    def _boolish(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)) and value in (0, 1):
            return bool(value)
        if isinstance(value, str):
            s = value.strip().lower()
            if s in {"true", "1", "yes", "y", "đúng", "dung"}:
                return True
            if s in {"false", "0", "no", "n", "sai"}:
                return False
        return None

    explicit = _boolish(option.get("is_correct"))
    if explicit is not None:
        is_correct = explicit
    else:
        answer = question.get("answer_json")

        values = []
        def _walk(x):
            if isinstance(x, dict):
                for v in x.values():
                    _walk(v)
            elif isinstance(x, (list, tuple)):
                for v in x:
                    _walk(v)
            elif x is not None:
                values.append(x)

        _walk(answer)

        option_key = str(option.get("key", "")).strip()
        option_text_vi = str(option.get("text_vi", "")).strip()
        option_text_en = str(option.get("text_en", "")).strip()

        candidates = {
            str(v).strip()
            for v in values
            if isinstance(v, (str, int, float, bool))
        }

        is_correct = (
            (option_key and option_key in candidates)
            or (option_text_vi and option_text_vi in candidates)
            or (option_text_en and option_text_en in candidates)
        )

    return {
        "qid": question_id,
        "key": option.get("key"),
        "text_vi": option.get("text_vi"),
        "text_en": option.get("text_en"),
        "is_correct": bool(is_correct),
    }


# V136_ACTIVATION_OPTION_HELPER
def _activation_option_params(question_id, option):
    """Return complete question_options params without relying on loop variable names."""
    def _boolish(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)) and value in (0, 1):
            return bool(value)
        if isinstance(value, str):
            s = value.strip().lower()
            if s in {"true", "1", "yes", "y", "đúng", "dung"}:
                return True
            if s in {"false", "0", "no", "n", "sai"}:
                return False
        return None

    explicit = _boolish(option.get("is_correct"))
    if explicit is not None:
        is_correct = explicit
    else:
        # Find the enclosing question object from the caller's local context.
        # This deliberately avoids assuming that the loop variable is named
        # `question`, `q`, `item`, etc.
        import inspect

        caller = inspect.currentframe().f_back
        seen = set()

        def _find_question(obj, depth=0):
            if depth > 5:
                return None
            oid = id(obj)
            if oid in seen:
                return None
            seen.add(oid)

            if isinstance(obj, dict):
                options = obj.get("options")
                if isinstance(options, list):
                    if any(candidate is option for candidate in options):
                        return obj

                for value in obj.values():
                    if isinstance(value, (dict, list, tuple)):
                        found = _find_question(value, depth + 1)
                        if found is not None:
                            return found

            elif isinstance(obj, (list, tuple)):
                for value in obj:
                    if isinstance(value, (dict, list, tuple)):
                        found = _find_question(value, depth + 1)
                        if found is not None:
                            return found

            return None

        enclosing_question = None
        if caller is not None:
            # First try direct local mappings; this is fast for the normal loop.
            for value in caller.f_locals.values():
                if isinstance(value, dict):
                    options = value.get("options")
                    if isinstance(options, list) and any(
                        candidate is option for candidate in options
                    ):
                        enclosing_question = value
                        break

            # Fallback: search nested draft/payload structures in caller locals.
            if enclosing_question is None:
                for value in caller.f_locals.values():
                    if isinstance(value, (dict, list, tuple)):
                        found = _find_question(value)
                        if found is not None:
                            enclosing_question = found
                            break

        if enclosing_question is None:
            raise ValueError(
                "Activation could not locate the enclosing question for an MCQ "
                "option missing is_correct."
            )

        answer = enclosing_question.get("answer_json")

        values = []

        def _walk(x):
            if isinstance(x, dict):
                for v in x.values():
                    _walk(v)
            elif isinstance(x, (list, tuple)):
                for v in x:
                    _walk(v)
            elif x is not None:
                values.append(x)

        _walk(answer)

        candidates = {
            str(v).strip()
            for v in values
            if isinstance(v, (str, int, float, bool))
        }

        option_key = str(option.get("key", "")).strip()
        option_text_vi = str(option.get("text_vi", "")).strip()
        option_text_en = str(option.get("text_en", "")).strip()

        is_correct = (
            (option_key and option_key in candidates)
            or (option_text_vi and option_text_vi in candidates)
            or (option_text_en and option_text_en in candidates)
        )

    return {
        "qid": question_id,
        "key": option.get("key"),
        "text_vi": option.get("text_vi"),
        "text_en": option.get("text_en"),
        "is_correct": bool(is_correct),
    }


def activate_latest_draft(db: Session, unit_code: str, *, force: bool = False) -> dict[str, Any]:
    draft = latest_draft(db, unit_code)
    payload = normalize_power_draft_payload(draft["payload_json"])
    validation = validate_power_draft(payload)
    if not validation["valid"]:
        raise ValueError("Draft is not valid: " + "; ".join(validation["errors"]))
    if draft.get("qa_status") != "passed" and not force:
        raise ValueError("Draft has not passed v1.3 QA; run build_power.py qa --unit ... first, or use --force")
    if draft["content_status"] != "ingested":
        raise ValueError("Unit content is not ingested")
    if draft["is_power_ready"] and not force:
        raise ValueError("Unit is already POWER-ready; pass --force to replace its generated package")

    canonical_primary = (
        str(_normalize_concept_code(draft.get("canonical_primary_concept_code")))
        if draft.get("canonical_primary_concept_code")
        else None
    )
    payload_primary = str(((payload.get("policy") or {}).get("primary_concept_code")) or "")
    if canonical_primary and payload_primary != canonical_primary:
        raise ValueError(
            "Refusing to replace canonical primary concept "
            f"{canonical_primary} with {payload_primary or '<missing>'}"
        )

    unit_id = draft["curriculum_unit_id"]
    concept_ids: dict[str, Any] = {}
    for concept in payload["concepts"]:
        concept_id = db.execute(
            text(
                """
                INSERT INTO concepts(code,name_vi,name_en,description_vi,description_en)
                VALUES (:code,:name_vi,:name_en,:description_vi,:description_en)
                ON CONFLICT (code) DO NOTHING
                RETURNING id
                """
            ),
            concept,
        ).scalar_one_or_none()
        if concept_id is None:
            concept_id = db.execute(text("SELECT id FROM concepts WHERE code=:code"), {"code": concept["code"]}).scalar_one()
        concept_ids[concept["code"]] = concept_id
        db.execute(
            text(
                """
                INSERT INTO curriculum_concepts(curriculum_unit_id,concept_id,is_core)
                VALUES (CAST(:unit_id AS uuid),:concept_id,:is_core)
                ON CONFLICT (curriculum_unit_id,concept_id) DO UPDATE SET is_core=EXCLUDED.is_core
                """
            ),
            {"unit_id": unit_id, "concept_id": concept_id, "is_core": bool(concept.get("is_core"))},
        )

    for rel in payload.get("relations") or []:
        db.execute(
            text(
                """
                INSERT INTO concept_relations(source_concept_id,target_concept_id,relation_type)
                VALUES (:source,:target,:relation_type)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "source": concept_ids[rel["source_code"]],
                "target": concept_ids[rel["target_code"]],
                "relation_type": rel["relation_type"],
            },
        )

    generation_metadata = {
        "generator": "POWER content build v1.2",
        "model": draft["model"],
        "draft_version": draft["version"],
        "source_fingerprint": draft["source_fingerprint"],
    }
    db.execute(
        text(
            """
            INSERT INTO power_unit_blueprints(
                curriculum_unit_id,version,prepare_json,work_json,policy_json,
                generation_metadata,validation_json,updated_at
            ) VALUES (
                CAST(:unit_id AS uuid),:version,CAST(:prepare AS jsonb),CAST(:work AS jsonb),
                CAST(:policy AS jsonb),CAST(:generation AS jsonb),CAST(:validation AS jsonb),now()
            )
            ON CONFLICT (curriculum_unit_id) DO UPDATE SET
                version=EXCLUDED.version,
                prepare_json=EXCLUDED.prepare_json,
                work_json=EXCLUDED.work_json,
                policy_json=EXCLUDED.policy_json,
                generation_metadata=EXCLUDED.generation_metadata,
                validation_json=EXCLUDED.validation_json,
                updated_at=now()
            """
        ),
        {
            "unit_id": unit_id,
            "version": draft["version"],
            "prepare": json.dumps(payload["prepare"], ensure_ascii=False),
            "work": json.dumps(payload["work"], ensure_ascii=False),
            "policy": json.dumps(payload["policy"], ensure_ascii=False),
            "generation": json.dumps(generation_metadata, ensure_ascii=False),
            "validation": json.dumps(validation, ensure_ascii=False),
        },
    )

    source_basis = db.execute(
        text(
            """
            SELECT s.code || ' PDF ' || cus.pdf_page_start || '-' || cus.pdf_page_end
            FROM curriculum_unit_sources cus JOIN sources s ON s.id=cus.source_id
            WHERE cus.curriculum_unit_id=CAST(:unit_id AS uuid) AND cus.source_role='primary'
            LIMIT 1
            """
        ),
        {"unit_id": unit_id},
    ).scalar_one_or_none() or "POWER v1.2 source-grounded draft"

    for index, q in enumerate(payload["questions"], start=1):
        qcode = _safe_question_code(unit_code, index)
        question_id = db.execute(
            text(
                """
                INSERT INTO questions(
                    code,question_type,difficulty,cognitive_level,stem_vi,stem_en,
                    answer_json,explanation_vi,explanation_en,source_basis,is_ai_generated,review_status
                ) VALUES (
                    :code,:question_type,:difficulty,:cognitive_level,:stem_vi,:stem_en,
                    CAST(:answer_json AS jsonb),:explanation_vi,:explanation_en,:source_basis,true,'approved'
                )
                ON CONFLICT (code) DO UPDATE SET
                    question_type=EXCLUDED.question_type,difficulty=EXCLUDED.difficulty,
                    cognitive_level=EXCLUDED.cognitive_level,stem_vi=EXCLUDED.stem_vi,stem_en=EXCLUDED.stem_en,
                    answer_json=EXCLUDED.answer_json,explanation_vi=EXCLUDED.explanation_vi,
                    explanation_en=EXCLUDED.explanation_en,source_basis=EXCLUDED.source_basis,
                    is_ai_generated=true,review_status='approved'
                RETURNING id
                """
            ),
            {
                **q,
                "code": qcode,
                "answer_json": json.dumps(q["answer_json"], ensure_ascii=False),
                "source_basis": source_basis,
            },
        ).scalar_one()
        db.execute(text("DELETE FROM question_options WHERE question_id=:id"), {"id": question_id})
        for option in q.get("options") or []:
            db.execute(
                text(
                    """
                    INSERT INTO question_options(question_id,option_key,text_vi,text_en,is_correct)
                    VALUES (:qid,:key,:text_vi,:text_en,:is_correct)
                    """
                ),
                _activation_option_params(question_id, option),
            )
        db.execute(text("DELETE FROM question_concepts WHERE question_id=:id"), {"id": question_id})
        db.execute(
            text(
                """
                INSERT INTO question_concepts(question_id,concept_id,is_primary)
                VALUES (:qid,:concept_id,true)
                """
            ),
            {"qid": question_id, "concept_id": concept_ids[q["concept_code"]]},
        )

    primary = payload["policy"]["primary_concept_code"]
    db.execute(
        text(
            """
            UPDATE curriculum_units
            SET is_power_ready=true,
                power_status='ready',
                metadata_json = COALESCE(metadata_json,'{}'::jsonb) || jsonb_build_object(
                    'primary_concept_code', CAST(:primary AS text),
                    'power_build', 'v1.2',
                    'power_draft_version', CAST(:version AS integer)
                )
            WHERE id=CAST(:unit_id AS uuid)
            """
        ),
        {"primary": primary, "version": draft["version"], "unit_id": unit_id},
    )
    db.execute(
        text(
            """
            UPDATE power_blueprint_drafts
            SET status='activated', validation_json=CAST(:validation AS jsonb), activated_at=now(), updated_at=now()
            WHERE id=CAST(:id AS uuid)
            """
        ),
        {"id": draft["id"], "validation": json.dumps(validation, ensure_ascii=False)},
    )
    return {
        "unit_code": unit_code,
        "draft_version": draft["version"],
        "concepts": len(payload["concepts"]),
        "questions": len(payload["questions"]),
        "primary_concept_code": primary,
        "power_ready": True,
    }
