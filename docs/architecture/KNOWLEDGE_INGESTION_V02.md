# POWER AI v0.2 — Knowledge ingestion foundation

## Goal

Prove the complete path:

`private source -> section -> chunk -> concept mapping -> embedding -> pgvector -> retrieval API`

without requiring an external AI key.

## Why `local_hash` embeddings exist

`local_hash` is a deterministic lexical hashing embedding used only for local development. It has the same 1536-dimensional database contract as the current `content_chunks.embedding` column, so ingestion and pgvector retrieval can be tested immediately. It is **not** intended to be the production semantic embedding model.

## Source manifests

Each private knowledge source is described by a JSON manifest. PDFs remain outside Git, normally under `private_sources/`. The manifest stores only source metadata, file location, section page ranges, and concept mappings.

For real textbooks, prefer verified section ranges instead of automatically treating the whole book as a single section.

## Windows local flow

From the repository root, with the API virtual environment activated:

```bat
python -m app.db.migrate
```

If you are at the repository root rather than `apps/api`, run:

```bat
cd apps\api
python -m app.db.migrate
cd ..\..
```

Ingest the POWER-owned smoke-test source:

```bat
python scripts\ingest\ingest_source.py --manifest content\sources\demo_dna_replication\manifest.json
```

Expected result contains `sections_created` and `chunks_created` greater than zero.

Then start the API and open Swagger:

```text
http://localhost:8000/docs
```

Call `POST /api/v1/retrieval/search`, for example:

```json
{
  "query": "Vì sao mạch chậm có các đoạn Okazaki?",
  "concept_code": "BIO.DNA.REPLICATION",
  "source_codes": ["POWER_DEMO_DNA"],
  "language": "vi",
  "top_k": 5
}
```

## Real SGK/Campbell ingestion

1. Put the PDF in `private_sources/` (ignored by Git).
2. Copy a manifest template.
3. Verify the chapter/section page ranges manually.
4. Map each section to existing POWER concept codes.
5. Run the same ingestion command.

Do not commit textbook PDFs or extracted copyrighted figures to the repository.
