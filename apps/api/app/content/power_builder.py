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


@dataclass(frozen=True)
class UnitSourceContext:
    unit: dict[str, Any]
    source_code: str
    source_title: str
    pdf_page_start: int
    pdf_page_end: int
    text: str
    fingerprint: str




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

    for relation in normalized.get("relations") or []:
        if isinstance(relation, dict):
            relation["source_code"] = _normalize_concept_code(relation.get("source_code"))
            relation["target_code"] = _normalize_concept_code(relation.get("target_code"))

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

    for concept in normalized.get("concepts") or []:
        if isinstance(concept, dict) and "is_core" in concept:
            concept["is_core"] = _coerce_bool(concept.get("is_core"))

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
- concepts: 4–8 concepts; 3–6 should be core. Codes must use canonical dotted identifiers: BIO.<DOMAIN>.<CONCEPT> (for example BIO.GENE.EXPRESSION). Never use BIO_GENE, BIO-GENE, spaces, or other separators.
- relations: 2–8 meaningful relationships among returned concepts.
- Prepare: 2–4 measurable outcomes and exactly 3 prerequisite/diagnostic items. Diagnostic items test prerequisite/readiness, not the whole lesson.
- Diagnostic MCQ uses expected as an option key string such as "A". Diagnostic true_false MUST use JSON boolean expected: true or false (never "true", "false", "Đúng", or "Sai") and options=[].
- Work: exactly 3 learner-owned tasks in both languages with matching task codes. Tasks should require explanation, comparison, analysis, interpretation, or application as supported by the source; never simply ask the learner to copy text.
- Questions: 8–10 source-grounded items, at least 3 MCQ and 3 true/false. Add short_answer only when a short canonical answer is genuinely unambiguous. MCQ has exactly 4 options with one correct option. true_false uses answer_json {{"value":true/false}} and options=[]. short_answer uses answer_json {{"value":"..."}} and options=[].
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

    if not payload.get("schema_version"):
        warnings.append("schema_version missing")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def save_draft(db: Session, *, unit_code: str, model: str, payload: dict[str, Any], fingerprint: str) -> dict[str, Any]:
    payload = normalize_power_draft_payload(payload)
    validation = validate_power_draft(payload)
    unit_id = db.execute(text("SELECT id FROM curriculum_units WHERE code=:code"), {"code": unit_code}).scalar_one()
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
                   cu.id::text AS curriculum_unit_id, cu.content_status, cu.is_power_ready,
                   cu.power_status, cu.name_vi, cu.name_en
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


def activate_latest_draft(db: Session, unit_code: str, *, force: bool = False) -> dict[str, Any]:
    draft = latest_draft(db, unit_code)
    payload = normalize_power_draft_payload(draft["payload_json"])
    validation = validate_power_draft(payload)
    if not validation["valid"]:
        raise ValueError("Draft is not valid: " + "; ".join(validation["errors"]))
    if draft["content_status"] != "ingested":
        raise ValueError("Unit content is not ingested")
    if draft["is_power_ready"] and not force:
        raise ValueError("Unit is already POWER-ready; pass --force to replace its generated package")

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
                {"qid": question_id, **option},
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
