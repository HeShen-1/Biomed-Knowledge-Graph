-- Add pg_trgm extension for faster ILIKE and substring search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Trigram GIN index for autocomplete/suggest performance
CREATE INDEX IF NOT EXISTS idx_entities_search_label_trgm
    ON entities_search USING GIN (label gin_trgm_ops);
