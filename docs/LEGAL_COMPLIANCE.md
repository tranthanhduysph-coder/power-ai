# Licensing and Release Compliance Checklist

This document is for POWER-AI-WEB maintainers.

## Current project licensing position

- Original POWER-AI-WEB materials: proprietary / all rights reserved unless explicitly stated otherwise.
- Public GitHub visibility is not intended as a blanket open-source grant.
- Third-party libraries retain their own licenses.
- Educational source content retains the rights of its original copyright holders.

## Release blocker: PyMuPDF / MuPDF

The ingestion pipeline imports and uses `pymupdf`.

For a proprietary SaaS or proprietary software release, resolve this before commercialization:
- obtain an Artifex commercial license; or
- replace PyMuPDF/MuPDF with a suitably licensed alternative; or
- adopt and comply with an AGPL-compatible deployment/source-disclosure model after legal review.

Do not describe the production system as "fully proprietary with no source obligations" while this dependency remains unresolved.

## Before each production release

1. Review `apps/web/package-lock.json` and `apps/api/requirements.txt`.
2. Generate a complete dependency and license inventory.
3. Preserve notices required by MIT, Apache-2.0, BSD, LGPL, AGPL, PostgreSQL, and other applicable licenses.
4. Confirm no copyrighted textbook PDFs or unauthorized figures are committed to the public repository or bundled for redistribution.
5. Confirm production secrets, user data, and private source documents are excluded.
6. Review the in-app legal notice and `THIRD_PARTY_NOTICES.md`.
7. Re-check service terms for AI, Firebase, hosting, storage, and payment providers.
