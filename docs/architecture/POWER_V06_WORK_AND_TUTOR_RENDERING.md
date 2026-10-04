# POWER AI v0.6 — Work evidence + rich Tutor rendering

## Product intent

POWER v0.6 turns **Work** from a static lesson card into a learner-owned evidence phase. The learner must process the content and leave evidence before moving to Evaluate. POWER Tutor scaffolds the work but does not replace the learner's response.

## Work evidence model

For the DNA replication vertical slice, Work contains three structured tasks:

1. directional constraint of DNA synthesis;
2. comparison of leading and lagging strands;
3. a cause-and-effect explanation culminating in Okazaki fragments.

Each task has a minimum learner-response length. Partial state can be saved at any time. Completing Work requires evidence for all tasks. The state stored in `power_phase_state` contains:

- `responses`
- `completed_tasks`
- `confidence_after`
- `evidence_chars`
- `completion_ratio`

The completion ratio is workflow evidence, **not a mastery score**.

## Tutor context

Tutor requests now receive the saved Prepare goal/readiness, Organize map and Work evidence when available. When reviewing an earlier phase, the requested phase is used for tutoring rather than assuming the current progression phase.

## Safe rich rendering

The model is instructed to return a small clean Markdown subset. The frontend converts that subset into semantic React/HTML elements (`p`, `h4`, `strong`, `em`, `ul`, `ol`, `blockquote`, `code`) without injecting raw model HTML. This prevents visible Markdown artifacts such as `**`, `###`, or list markers while avoiding `dangerouslySetInnerHTML`.

Raw HTML, decorative symbols, emoji and Markdown tables are discouraged in the Tutor prompt. Tables remain a structured Tutor block rendered by the application.

## Progression rule

When Work is completed while Work is the current progression phase:

`WORK → EVALUATE`

Reviewing or editing a completed Work phase does not move the progression backward.
