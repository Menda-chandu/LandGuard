"""Dataset import and API tests using isolated storage, without an OCR binary."""
import io
from pathlib import Path
import sys
import zipfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "database"))

from import_dataset import ASSET_NAMES, import_dataset
from app.api import dashboard, documents
from app.config import settings
from app.database import Base, get_db
from app.models import DocumentRecord, LandRecord, OwnershipHistory, RiskAssessment, VerificationResult


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        yield session
    engine.dispose()


def make_archive(missing=None):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as z:
        for name in ASSET_NAMES:
            path = ROOT / "sample_data" / name
            if path.is_file() and name != missing:
                z.writestr(f"sample_data/{name}", path.read_bytes())
    archive.seek(0)
    return archive


def client_for(db):
    app = FastAPI()
    app.include_router(dashboard.router, prefix="/api/dashboard")
    app.include_router(documents.router, prefix="/api/documents")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def upload_row():
    return DocumentRecord(document_id="KEEP-ME", filename="existing.pdf", file_path="existing.pdf",
                          file_type="PDF", file_size_bytes=10, ocr_status="COMPLETED")


def test_import_is_repeatable_and_preserves_existing_uploads(db, tmp_path):
    db.add(upload_row())
    db.commit()
    first = import_dataset(make_archive(), db, tmp_path)
    second = import_dataset(make_archive(), db, tmp_path)
    assert first == second
    assert db.query(LandRecord).count() == 122
    assert db.query(OwnershipHistory).count() == 220
    assert db.query(DocumentRecord).one().document_id == "KEEP-ME"
    assert (tmp_path / "LandGuard_Synthetic_Test_Land_Record.pdf").read_bytes().startswith(b"%PDF")


def test_missing_dataset_file_does_not_modify_database(db, tmp_path):
    with pytest.raises(ValueError, match="Required dataset file is missing"):
        import_dataset(make_archive(missing="synthetic_ownership_history_100.csv"), db, tmp_path)
    assert db.query(LandRecord).count() == 0
    assert db.query(OwnershipHistory).count() == 0
    assert list(tmp_path.iterdir()) == []


def test_dashboard_uses_persisted_results_and_distinguishes_unassessed(db):
    db.add(upload_row())
    db.commit()
    with client_for(db) as client:
        data = client.get("/api/dashboard").json()
        assert data["stats"]["uploaded_documents"] == 1
        assert data["stats"]["checked_documents"] == 0
        assert data["stats"]["average_risk_score"] is None
        assert data["recent_documents"][0]["verification_status"] == "NOT_CHECKED"
        assert data["recent_documents"][0]["risk_score"] is None
        db.add(VerificationResult(verification_id="VER-1", document_id="KEEP-ME", verification_status="SUSPICIOUS"))
        db.commit()
        db.add(RiskAssessment(assessment_id="RISK-1", verification_id="VER-1", risk_score=35, risk_level="MEDIUM"))
        db.commit()
        data = client.get("/api/dashboard").json()
        assert data["stats"]["checked_documents"] == 1
        assert data["stats"]["suspicious_documents"] == 1
        assert data["stats"]["verified_documents"] == 0
        assert data["stats"]["average_risk_score"] == 35
        assert data["recent_documents"][0]["risk_score"] == 35


def test_dataset_sample_download_and_upload_uses_original_pdf(db, tmp_path, monkeypatch):
    assets = tmp_path / "assets"
    import_dataset(make_archive(), db, assets)
    monkeypatch.setattr(settings, "DATASET_DIR", assets)
    monkeypatch.setattr(documents, "UPLOADS_DIR", str(tmp_path / "uploads"))
    filename = "LandGuard_Synthetic_Test_Land_Record.pdf"
    with client_for(db) as client:
        samples = client.get("/api/documents/samples").json()["samples"]
        assert len(samples) == 5
        response = client.get(f"/api/documents/samples/{filename}")
        assert response.status_code == 200
        assert response.content == (assets / filename).read_bytes()
        assert client.get("/api/documents/samples/missing.pdf").status_code == 404
        response = client.post("/api/documents/upload", files={"file": (filename, response.content, "application/pdf")})
        assert response.status_code == 201
        assert response.json()["ocr_status"] == "COMPLETED"
        assert response.json()["extracted_nlp_fields"]["owner_name"] == "Arun Kumar"
        assert db.query(DocumentRecord).count() == 1
