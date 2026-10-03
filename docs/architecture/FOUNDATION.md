# POWER AI foundation decisions

## 1. Product boundary

POWER AI is a new commercial product. It does not inherit runtime code, database state or experiment-specific assumptions from the previous GOFAI project.

## 2. Pedagogical invariant

The learning workflow is the POWER cycle:

1. Prepare
2. Organize
3. Work
4. Evaluate
5. Rethink

The phase state is persisted in the database and is therefore part of the product model, not only prompt text.

## 3. Knowledge boundary

The first commercial Biology knowledge base is intentionally constrained to four source books:

- Biology 10 KNTT
- Biology 11 KNTT
- Biology 12 KNTT
- Campbell Biology

KNTT determines curriculum scope and sequencing. Campbell acts as a reference source for deeper explanation and English terminology. The runtime retrieves small concept-linked chunks instead of repeatedly sending complete books to a model.

## 4. Concept-first storage

Books are sources. Concepts are the shared semantic layer. Curriculum units, source sections, questions and visuals map to concepts.

This lets the same learner model survive later expansion to Natural Science (KHTN) grades 6–9.

## 5. Authentication

Firebase Authentication owns identity:

- Google account
- email/password

FastAPI verifies Firebase ID tokens with the Firebase Admin SDK and maps `firebase_uid` to an internal POWER UUID. All learning data uses the internal UUID.

## 6. Learner data model

POWER stores both:

- immutable/append-style raw observations: learning events and question attempts
- derived current state: concept mastery, misconception state and recommendations

This allows mastery algorithms to be replaced later without losing source observations.

## 7. Practice engine

Required item types:

- MCQ
- true/false
- short answer

Two modes:

- custom: learner selects topic, difficulty, item types and count
- adaptive: engine prioritizes weak concepts using current mastery and recent attempt history

Question sourcing order for later versions:

1. reviewed question bank
2. deterministic/template generation
3. LLM generation only when needed

## 8. Billing readiness

Billing is modeled as products, plans and entitlements rather than a single `is_pro` flag. Biology is the first product. Later KHTN 6–9 can be added as another content entitlement without rewriting the learning engine.

## 9. AI boundary

The web client never calls an AI provider directly. All model calls must pass through FastAPI, where authentication, usage logging, learner context and entitlements can be enforced.

The v0.1 Tutor is intentionally a mock structured provider. This proves the front-end renderer contract before a paid model is connected.
