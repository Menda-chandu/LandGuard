"""Idempotent additive migrations for existing SQLite and PostgreSQL databases."""
from sqlalchemy import inspect, text


def upgrade_document_evidence(engine):
    columns = {c["name"] for c in inspect(engine).get_columns("document_records")}
    with engine.begin() as connection:
        for name, datatype in (("content_sha256", "VARCHAR(64)"), ("text_sha256", "VARCHAR(64)"), ("claimed_geometry", "TEXT")):
            if name not in columns:
                connection.execute(text(f"ALTER TABLE document_records ADD COLUMN {name} {datatype}"))
        for name in ("content_sha256", "text_sha256"):
            connection.execute(text(f"CREATE INDEX IF NOT EXISTS ix_document_records_{name} ON document_records ({name})"))
