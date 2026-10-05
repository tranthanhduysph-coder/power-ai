# POWER AI v1.2.2 — Canonical concept identifiers

POWER concept identifiers use dotted uppercase ontology codes (`BIO.GENE`, `BIO.GENE.EXPRESSION`).
Model outputs may drift to underscore or hyphen separators. The builder now canonicalizes BIO-prefixed separators consistently across concepts, relations, Prepare diagnostics, Work tasks, policy, and Evaluate questions before strict validation.

Normalization does not accept arbitrary non-BIO codes and does not hide collisions; duplicate codes after normalization remain validation errors.
