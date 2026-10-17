-- Additive PostgreSQL migration. The application also applies it idempotently.
ALTER TABLE document_records ADD COLUMN IF NOT EXISTS content_sha256 VARCHAR(64);
ALTER TABLE document_records ADD COLUMN IF NOT EXISTS text_sha256 VARCHAR(64);
ALTER TABLE document_records ADD COLUMN IF NOT EXISTS claimed_geometry TEXT;
CREATE INDEX IF NOT EXISTS ix_document_records_content_sha256 ON document_records(content_sha256);
CREATE INDEX IF NOT EXISTS ix_document_records_text_sha256 ON document_records(text_sha256);
