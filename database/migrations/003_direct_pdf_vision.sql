-- POWER AI v0.3 — direct PDF / vision extraction provenance

CREATE TABLE IF NOT EXISTS source_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    printed_page_label TEXT,
    text_content TEXT NOT NULL DEFAULT '',
    visuals_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    extraction_method TEXT NOT NULL DEFAULT 'native_text',
    extraction_provider TEXT,
    extraction_model TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(source_id, page_number)
);

CREATE INDEX IF NOT EXISTS idx_source_pages_source_page
    ON source_pages(source_id, page_number);
