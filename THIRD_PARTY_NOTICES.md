# Third-Party and Open-Source Notices

POWER-AI-WEB uses third-party software. Each third-party component remains subject to its own license. This file is a practical notice for the main direct dependencies and is not a substitute for the complete license texts bundled with, referenced by, or distributed with those packages.

## Frontend

| Component | Current project use | License |
| --- | --- | --- |
| Next.js | Web application framework | MIT |
| React / React DOM | User interface runtime | MIT |
| Firebase JavaScript SDK | Authentication/client services | Apache-2.0 |
| TypeScript and @types packages | Development/tooling | Their respective upstream licenses |

The installed dependency graph is recorded in `apps/web/package-lock.json`. Transitive dependencies retain their own licenses.

## Backend

| Component | Current project use | License / note |
| --- | --- | --- |
| FastAPI | API framework | MIT |
| Uvicorn | ASGI server | BSD-3-Clause |
| SQLAlchemy | ORM / SQL toolkit | MIT |
| Psycopg | PostgreSQL driver | LGPL-3.0-only (upstream terms apply) |
| Pydantic / pydantic-settings | Validation/settings | MIT |
| Firebase Admin SDK | Authentication/admin integration | Apache-2.0 |
| python-dotenv | Environment configuration | BSD-3-Clause |
| pypdf | PDF processing | BSD-3-Clause |
| OpenAI Python SDK | AI API client | Apache-2.0 |
| pytest | Testing | MIT |
| PyMuPDF / MuPDF | PDF rendering and extraction | GNU AGPL v3 or a commercial license from Artifex |

The backend dependency ranges are recorded in `apps/api/requirements.txt`.

## Important PyMuPDF / MuPDF licensing note

POWER-AI-WEB currently uses PyMuPDF in the PDF ingestion pipeline. PyMuPDF is offered under the GNU Affero General Public License (AGPL) and a commercial licensing option.

A proprietary or closed-source production deployment must not assume that the repository's proprietary notice overrides PyMuPDF/MuPDF obligations. Before deploying POWER-AI-WEB as proprietary SaaS or distributing it as proprietary software, the project must do one of the following:

1. comply with the applicable AGPL obligations for the deployment; or
2. obtain an appropriate commercial license from Artifex; or
3. replace PyMuPDF/MuPDF with a dependency whose license is compatible with the intended deployment model.

This is a release-blocking licensing item for proprietary commercialization until resolved.

## Infrastructure

PostgreSQL, pgvector, Docker/container images, operating-system packages, and managed cloud services are governed by their own terms and licenses.

## Educational and reference content

Textbooks, publisher PDFs, figures, Campbell Biology materials, and other third-party educational sources are not open-sourced by POWER-AI-WEB and are not covered by the proprietary software notice or by the licenses of the software dependencies.

## AI services

Use of third-party AI, authentication, hosting, or cloud APIs is also governed by the applicable service terms in addition to any SDK license.

## Maintenance

Before a public production release or software distribution:
- regenerate or audit the complete dependency-license inventory;
- retain license and attribution notices required by dependencies;
- resolve any strong-copyleft/commercial-license dependencies, especially PyMuPDF/MuPDF;
- verify rights for all bundled educational content, images, fonts, datasets, and branding assets.

This notice is informational and should be reviewed as the dependency tree changes.
