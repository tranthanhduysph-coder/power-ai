POWER AI v0.4 patch

Scope: POWER learning-cycle foundation, with a complete PREPARE vertical slice.

Backend:
- SMART goal feedback service
- prerequisite diagnostic blueprint/scoring
- active POWER session resume
- structured Prepare persistence
- phase-aware Tutor context
- RETHINK closes a learning cycle
- active cycle exposed in progress API

Frontend:
- real Prepare workflow: outcomes, learner goal, SMART check, duration, confidence, prior knowledge, prerequisite diagnostic
- phase completion state in the POWER stepper
- phase-specific Organize / Work / Evaluate / Rethink screens
- phase-aware Tutor UI
- dashboard shows active POWER phase

Validation performed in build environment:
- python compileall: PASS
- pytest: 9 passed
- TypeScript/TSX syntax parse: PASS
- full npm/Next build could not be completed in the build container because dependency installation timed out; run npm run build locally after applying the patch.
