# POWER AI v1.2.1 — Content Builder Boolean Normalization

This hotfix hardens POWER package generation against harmless JSON type drift from the content model.

- `true_false` diagnostic `expected` is normalized from unambiguous values such as `"true"`, `"false"`, `"Đúng"`, `"Sai"`, `1`, and `0` to real JSON booleans.
- `true_false` question `answer_json.value`, MCQ option `is_correct`, and concept `is_core` receive the same safe normalization.
- Strict validation still runs after normalization; ambiguous values remain validation errors.
- The generation prompt now explicitly requires real JSON booleans for true/false diagnostics.
