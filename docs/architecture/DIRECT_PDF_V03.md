# POWER AI v0.3 — Direct PDF vision ingestion

## Decision

POWER AI keeps the original PDF as the source of truth. It does not require users or maintainers to convert PDFs to Markdown or DOCX before ingestion.

The reader works page by page:

```text
PDF page
  ├─ usable text layer -> PyMuPDF native text
  └─ image-only / weak text layer -> render page in memory -> vision model
                                                ↓
                                      text + printed page + visuals
                                                ↓
                                           source_pages
                                                ↓
                                  page-preserving chunks + concepts
                                                ↓
                                      embeddings -> pgvector
```

No searchable PDF, Markdown or DOCX derivative is created as a required preprocessing step.

## Why page-by-page

- Exact PDF page provenance is preserved.
- Only pages in the manifest are processed, avoiding an expensive whole-book pass during development.
- Image-only textbook pages can be understood without a separate OCR installation.
- Page extraction is cached under `storage/ingestion-cache/<document-sha256>/` so a rerun does not repeatedly call the vision provider.
- Tables, diagrams and figures are described in structured page metadata.

## `source_pages`

Migration `003_direct_pdf_vision.sql` adds a page-level source table with:

- PDF page number
- printed textbook page label when visible
- extracted page text
- visual metadata
- extraction method/provider/model

Chunks keep the exact PDF page number in `page_start` / `page_end` and carry the printed page label plus visual metadata in `metadata_json`.

## Providers

Local plumbing can still use:

```env
AI_PROVIDER=mock
EMBEDDING_PROVIDER=local_hash
VISION_PROVIDER=disabled
```

Real scanned-PDF ingestion and grounded Tutor use server-side OpenAI API configuration:

```env
OPENAI_API_KEY=...
VISION_PROVIDER=openai
VISION_MODEL=gpt-5.6-luna
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
AI_PROVIDER=openai
TUTOR_MODEL=gpt-5.6-luna
```

The browser never receives `OPENAI_API_KEY`.

## Pilot source

The v0.3 patch includes one real-source vertical slice:

- Source: `BIO12_KNTT`
- Section: Bài 1 — DNA và cơ chế tái bản DNA
- PDF pages: 7–10
- POWER unit: `B12_DNA_REPLICATION`

This matches the existing DNA-replication Tutor and Practice vertical slice, while replacing the v0.2 demo knowledge source with real textbook retrieval.

## Expansion path

After this pilot is verified, add the remaining sections to the manifests for Biology 10, 11 and 12. Campbell can use native PDF text extraction when its PDF has a usable text layer; image-only pages automatically fall back to the same vision path.
