"""Copy an existing SQLite database into PostgreSQL, preserving document IDs.

Run from the project root: .venv/bin/python database/migrate_sqlite_to_postgres.py .venv/landguard.db
Existing conflicting target rows cause a rollback instead of being overwritten.
"""
import argparse
from pathlib import Path
import sys
from sqlalchemy import create_engine, inspect, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.database import Base, engine, SessionLocal
from app.models import LandRecord, OwnershipHistory, DocumentRecord, VerificationResult, RiskAssessment
from app.migrations import upgrade_document_evidence
from app.document_processing.fingerprints import file_fingerprint, text_fingerprint


def migrate(source_path):
    if engine.dialect.name != "postgresql":
        raise ValueError("Configure a PostgreSQL destination before running this migration.")
    if not Path(source_path).is_file():
        raise ValueError("Source SQLite database does not exist.")
    Base.metadata.create_all(engine)
    upgrade_document_evidence(engine)
    source = create_engine(f"sqlite:///{Path(source_path).resolve()}")
    counts = {}
    with source.connect() as connection, SessionLocal() as db:
        for model in (LandRecord, OwnershipHistory, DocumentRecord, VerificationResult, RiskAssessment):
            available = {c["name"] for c in inspect(source).get_columns(model.__tablename__)}
            columns = [c for c in model.__table__.columns if c.name in available]
            rows = connection.execute(select(*columns)).mappings().all()
            key = list(model.__table__.primary_key.columns)[0].name
            for row in rows:
                values = dict(row)
                existing = db.get(model, values[key])
                if existing:
                    if any(getattr(existing, k) != v for k, v in values.items() if k not in ("content_sha256", "text_sha256")):
                        raise ValueError(f"Conflicting destination row: {model.__tablename__}/{values[key]}")
                else:
                    db.add(model(**values))
            db.flush()
            counts[model.__tablename__] = len(rows)
        for document in db.query(DocumentRecord).all():
            path = (ROOT / document.file_path).resolve()
            if path.is_relative_to(ROOT / "uploads") and path.is_file():
                document.content_sha256 = file_fingerprint(path)
            document.text_sha256 = text_fingerprint(document.extracted_text)
        db.commit()
    source.dispose()
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    print(migrate(parser.parse_args().source))
