CREATE TABLE IF NOT EXISTS entities_search (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT,
    search_vector TSVECTOR,
    search_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_entities_search_vector ON entities_search USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_entities_search_type ON entities_search(type);

CREATE TABLE IF NOT EXISTS ingest_status (
    source TEXT PRIMARY KEY,
    last_sync_at TIMESTAMPTZ,
    status TEXT DEFAULT 'idle',
    records_added INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ingest_log (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running',
    message TEXT
);

INSERT INTO ingest_status (source) VALUES
    ('pubmed'), ('uniprot'), ('chembl'), ('opentargets'), ('string')
ON CONFLICT (source) DO NOTHING;
