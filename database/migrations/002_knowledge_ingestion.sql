-- POWER AI v0.2 — knowledge ingestion foundation
-- Adds ingestion provenance, many-to-many chunk/concept mapping, job tracking,
-- and a vector index while preserving the v0.1 schema.

ALTER TABLE sources
    ADD COLUMN IF NOT EXISTS content_sha256 TEXT,
    ADD COLUMN IF NOT EXISTS ingest_status TEXT NOT NULL DEFAULT 'not_ingested',
    ADD COLUMN IF NOT EXISTS metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE source_sections
    ADD COLUMN IF NOT EXISTS section_level INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE content_chunks
    ADD COLUMN IF NOT EXISTS chunk_index INTEGER,
    ADD COLUMN IF NOT EXISTS content_hash TEXT,
    ADD COLUMN IF NOT EXISTS metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS embedding_provider TEXT,
    ADD COLUMN IF NOT EXISTS embedding_model TEXT,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE UNIQUE INDEX IF NOT EXISTS uq_content_chunks_section_index
    ON content_chunks(source_id, section_id, chunk_index)
    WHERE section_id IS NOT NULL AND chunk_index IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_content_chunks_source ON content_chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_source_sections_source_sort ON source_sections(source_id, sort_order);

CREATE TABLE IF NOT EXISTS content_chunk_concepts (
    chunk_id UUID NOT NULL REFERENCES content_chunks(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    relevance NUMERIC(6,5) NOT NULL DEFAULT 1.0,
    mapping_method TEXT NOT NULL DEFAULT 'explicit',
    PRIMARY KEY(chunk_id, concept_id)
);
CREATE INDEX IF NOT EXISTS idx_content_chunk_concepts_concept
    ON content_chunk_concepts(concept_id, chunk_id);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    source_code TEXT NOT NULL,
    manifest_path TEXT,
    document_path TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    embedding_provider TEXT,
    embedding_model TEXT,
    sections_created INTEGER NOT NULL DEFAULT 0,
    chunks_created INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_source_time
    ON ingestion_jobs(source_code, started_at DESC);

-- pgvector cosine index. This is safe for an initially empty/small table and
-- becomes useful as the knowledge base grows.
CREATE INDEX IF NOT EXISTS idx_content_chunks_embedding_hnsw
    ON content_chunks USING hnsw (embedding vector_cosine_ops)
    WHERE embedding IS NOT NULL;
