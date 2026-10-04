# POWER AI v0.8 — Rethink + Learner Model

v0.8 replaces the generic Rethink textarea with an evidence-based reflection flow.

## Product rule

Rethink does not diagnose a learner from one wrong answer. POWER first presents **candidate misconception signals** derived from Evaluate question evidence. The learner confirms only the statements that genuinely match their prior thinking. Only confirmed misconceptions are written to the durable learner model.

## Data flow

```text
Evaluate question_attempts
        ↓
question_misconceptions rules
        ↓
candidate misconception signals
        ↓
learner confirmation in Rethink
        ↓
learner_misconceptions
misconception_evidence
        ↓
structured reflection
        ↓
learning_recommendations
        ↓
next POWER cycle / targeted practice
```

## Rethink evidence

The learner records:

- what became clearer;
- the main cause of error/uncertainty;
- the corrected explanation in their own words;
- one concrete action for the next learning attempt;
- confidence after Rethink;
- optional confirmation of misconception candidates.

Rethink can only close a POWER cycle when database-backed Evaluate evidence exists.

## New database objects

- `question_misconceptions`: deterministic evidence rules connecting questions to misconception candidates;
- `misconception_evidence`: append-only evidence supporting a learner misconception record;
- `learning_recommendations`: durable next-action recommendations for Dashboard and future adaptive orchestration.

## Recommendation policy in v0.8

The initial policy is deterministic and inspectable:

1. low Evaluate accuracy, several weak concepts, or a confirmed misconception → review and retry;
2. moderate evidence or low confidence → targeted adaptive practice;
3. strong evidence with no weak concept → ready to continue.

A later version may replace the rule policy, but the persisted recommendation contract remains stable.
