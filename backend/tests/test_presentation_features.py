"""Evidence tests run against SQLite and an isolated PostgreSQL schema.

Set TEST_POSTGRES=1 to exercise PostgreSQL using the configured local connection.
No application data is modified by these tests.
"""
import json
import os
from pathlib import Path
import sys
from datetime import date
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.database import Base, get_db
from app.config import settings
from app.models import LandRecord, OwnershipHistory, DocumentRecord, RiskAssessment
from app.api import documents
from app.document_processing.fingerprints import text_fingerprint
from app.verification.engine import verification_engine
from app.gis.spatial_engine import gis_spatial_engine
from app.gis.boundaries import compare_boundaries, validate_geometry
from app.nlp.extractor import nlp_engine
from app.ocr.processor import process_document_ocr
from app.risk_scoring.engine import risk_scoring_engine
from app.risk_scoring.ml import assess_reference_outlier


def rectangle(left=78, right=78.001):
    return {"type": "Polygon", "coordinates": [[[left, 17], [right, 17], [right, 17.001], [left, 17.001], [left, 17]]]}


@pytest.fixture(params=["sqlite", "postgres"])
def db(request, monkeypatch):
    schema = None
    if request.param == "postgres":
        if os.getenv("TEST_POSTGRES") != "1":
            pytest.skip("Set TEST_POSTGRES=1 for isolated PostgreSQL tests")
        base_engine = create_engine(settings.DATABASE_URL)
        schema = "landguard_test_" + uuid.uuid4().hex
        with base_engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = base_engine.execution_options(schema_translate_map={None: schema})
    else:
        base_engine = engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    original = {"type": "Feature", "properties": {"survey_number": "SYN-101/A", "village": "Narsingi", "mandal": "Gandipet", "district": "Ranga Reddy",
                "boundary_details": {"north": "Demo road", "south": "Demo drain", "east": "Survey SYN-102/A", "west": "Demo lane"}}, "geometry": rectangle()}
    neighbor = {"type": "Feature", "properties": {"survey_number": "SYN-102/A"}, "geometry": rectangle(78.001, 78.002)}
    monkeypatch.setattr(gis_spatial_engine, "geojson_data", {"type": "FeatureCollection", "features": [original, neighbor]})
    try:
        with sessionmaker(bind=engine)() as session:
            session.add(LandRecord(record_id="R1", survey_number="SYN-101/A", owner_name="Kalyan Varma Dantuluri", land_area_acres=2.2,
                                   village="Narsingi", mandal="Gandipet", district="Ranga Reddy", state="Telangana", document_type="Gift Deed",
                                   registration_number="REG-2020-001", registration_date=date(2020, 3, 15)))
            session.add(OwnershipHistory(history_id="H1", survey_number="SYN-101/A", owner_name="Kalyan Varma Dantuluri", transfer_date=date(2020, 3, 15), transfer_type="Gift Deed"))
            session.commit()
            yield session
    finally:
        if schema:
            with base_engine.begin() as conn:
                conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        base_engine.dispose()


def deed_text(registration="REG-2020-001", registration_date="15 March 2020"):
    return f"Document type: Gift Deed\nOwner name: Kalyan Varma Dantuluri\nSurvey number: SYN-101/A\nLand area: 2.2 acres\nVillage: Narsingi\nMandal: Gandipet\nDistrict: Ranga Reddy\nDocument number: {registration}\nRegistration date: {registration_date}\n"


def save_doc(db, identity="D1", content=None, **kwargs):
    content = deed_text() if content is None else content
    row = DocumentRecord(document_id=identity, filename="deed.pdf", file_path="uploads/deed.pdf", file_type="PDF", file_size_bytes=100,
                         extracted_text=content, extracted_owner_name="Kalyan Varma Dantuluri", extracted_survey_number="SYN-101/A",
                         extracted_land_area=2.2, text_sha256=text_fingerprint(content), **kwargs)
    db.add(row)
    db.commit()
    return row


def test_registration_number_and_date_are_cross_checked(db):
    save_doc(db)
    result = verification_engine.verify_document("D1", db)
    assert result["evidence_checks"]["registration_number"]["status"] == "MATCH"
    assert result["evidence_checks"]["registration_date"]["status"] == "MATCH"
    wrong = save_doc(db, "D2", deed_text("FAKE-9999", "2021-03-15"))
    result = verification_engine.verify_document(wrong.document_id, db)
    types = {a["type"] for a in result["detected_anomalies"]}
    assert {"REGISTRATION_NUMBER_MISMATCH", "REGISTRATION_DATE_MISMATCH"} <= types
    assert result["verification_status"] == "SUSPICIOUS"


def test_missing_boundary_and_registration_are_never_reported_as_matches(db):
    save_doc(db, content="Owner name: Kalyan Varma Dantuluri\nSurvey number: SYN-101/A\nLand area: 2.2 acres\n")
    result = verification_engine.verify_document("D1", db)
    assert result["evidence_checks"]["registration_number"]["status"] == "NOT_PROVIDED"
    assert result["field_matches"]["registration_number_match"] is None
    assert result["evidence_checks"]["boundary_geometry"]["status"] == "NOT_PROVIDED"
    assert result["field_matches"]["boundary_match"] is None


def test_duplicate_files_and_normalized_text_are_evidence_not_owner_matches(db):
    save_doc(db, content_sha256="a" * 64)
    save_doc(db, "D2", deed_text().upper().replace("\n", "  "), content_sha256="b" * 64)
    result = verification_engine.verify_document("D2", db)
    assert result["evidence_checks"]["duplicate_document"]["matches"] == [{"document_id": "D1", "evidence": "IDENTICAL_NORMALIZED_TEXT"}]
    save_doc(db, "D3", deed_text("REG-2020-002"), content_sha256="a" * 64)
    result = verification_engine.verify_document("D3", db)
    assert result["evidence_checks"]["duplicate_document"]["matches"] == [{"document_id": "D1", "evidence": "IDENTICAL_FILE"}]


def test_boundary_geometry_detects_encroachment_and_missing_land(db):
    document = save_doc(db, claimed_geometry=json.dumps(rectangle()))
    result = verification_engine.verify_document("D1", db)
    assert result["field_matches"]["boundary_match"] is True
    document.claimed_geometry = json.dumps(rectangle(78.0005, 78.0015))
    db.commit()
    result = verification_engine.verify_document("D1", db)
    geometry = result["evidence_checks"]["boundary_geometry"]
    assert geometry["status"] == "MISMATCH"
    assert geometry["outside_area_acres"] > 0
    assert geometry["missing_area_acres"] > 0
    assert geometry["overlapping_parcels"][0]["survey_number"] == "SYN-102/A"
    assert {"BOUNDARY_GEOMETRY_MISMATCH", "PARCEL_ENCROACHMENT"} <= {a["type"] for a in result["detected_anomalies"]}


def test_boundary_description_mismatch_is_checked_when_reference_exists(db):
    save_doc(db, content=deed_text() + "North: Different road\nSouth: Demo drain\nEast: Survey SYN-102/A\nWest: Demo lane\n")
    result = verification_engine.verify_document("D1", db)
    assert result["evidence_checks"]["boundary_descriptions"]["north"]["status"] == "MISMATCH"
    assert result["evidence_checks"]["boundary_descriptions"]["south"]["status"] == "MATCH"
    assert any(a["type"] == "BOUNDARY_DESCRIPTION_MISMATCH" for a in result["detected_anomalies"])


def test_boundary_api_and_duplicate_upload_survive_database_round_trip(db, monkeypatch, tmp_path):
    monkeypatch.setattr(documents, "UPLOADS_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "KEEP_LOCAL_UPLOADS", False)
    monkeypatch.setattr(documents, "process_document_ocr", lambda _: {"status": "COMPLETED", "text": deed_text(), "confidence": 99})
    app = FastAPI()
    app.include_router(documents.router, prefix="/api/documents")
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        first = client.post("/api/documents/upload", files={"file": ("original.pdf", b"synthetic PDF bytes", "application/pdf")})
        assert first.status_code == 201
        assert list(tmp_path.iterdir()) == []
        original = client.get(f"/api/documents/{first.json()['document_id']}/file")
        assert original.status_code == 200
        assert original.content == b"synthetic PDF bytes"
        second = client.post("/api/documents/upload", files={"file": ("renamed.pdf", b"synthetic PDF bytes", "application/pdf")})
        assert second.json()["duplicate_documents"][0]["evidence"] == "IDENTICAL_FILE"
        identity = first.json()["document_id"]
        response = client.put(f"/api/documents/{identity}/boundary", json=rectangle())
        assert response.status_code == 200
        assert response.json()["field_matches"]["boundary_match"] is True
        assert client.get(f"/api/documents/{identity}").json()["claimed_geometry"] == rectangle()
        for invalid in ({"type": "Point", "coordinates": [78, 17]}, rectangle(78, 78), {"type": "Polygon", "coordinates": [[[78, 17], [78.001, 17.001], [78, 17.001], [78.001, 17], [78, 17]]]}, {"type": "Polygon", "coordinates": [[[78, 17], [79, 18]]]}):
            assert client.put(f"/api/documents/{identity}/boundary", json=invalid).status_code == 422
        assert client.put("/api/documents/missing/boundary", json=rectangle()).status_code == 404
    # Reassessment deletes old dependent risk rows, also under PostgreSQL FKs.
    risk_scoring_engine.compute_risk_assessment(identity, db)
    assessment = risk_scoring_engine.compute_risk_assessment(identity, db)
    assert db.query(RiskAssessment).count() == 1
    assert assessment["recommendation"] == "Manual review recommended for flagged inconsistencies"


def test_demo_seeding_is_repeatable_and_preserves_existing_registry_edits():
    from app.seed import seed_demo_registry
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        assert seed_demo_registry(session, ROOT / "sample_data") is True
        assert session.query(LandRecord).count() == 122
        assert session.query(OwnershipHistory).count() == 220
        record = session.get(LandRecord, "SYN-REC-001")
        record.owner_name = "Updated demo owner"
        session.commit()
        assert seed_demo_registry(session, ROOT / "sample_data") is False
        assert session.get(LandRecord, "SYN-REC-001").owner_name == "Updated demo owner"
    engine.dispose()


def test_health_remains_responsive_while_document_ocr_is_running(db, monkeypatch, tmp_path):
    from app.api import health
    started, release = Event(), Event()

    def slow_ocr(_):
        started.set()
        assert release.wait(timeout=10), "Test did not release OCR"
        return {"status": "COMPLETED", "text": deed_text(), "confidence": 99}

    monkeypatch.setattr(documents, "UPLOADS_DIR", str(tmp_path))
    monkeypatch.setattr(documents, "process_document_ocr", slow_ocr)
    monkeypatch.setattr(health, "check_db_connection", lambda: {"status": "connected"})
    app = FastAPI()
    app.include_router(documents.router, prefix="/api/documents")
    app.include_router(health.router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client, ThreadPoolExecutor(max_workers=2) as requests:
        upload = requests.submit(client.post, "/api/documents/upload", files={"file": ("scan.png", b"scan", "image/png")})
        try:
            assert started.wait(timeout=5)
            response = requests.submit(client.get, "/api/health").result(timeout=2)
            assert response.status_code == 200
            assert not upload.done()
        finally:
            release.set()
        assert upload.result(timeout=5).status_code == 201


def test_health_check_returns_unhealthy_status_when_database_is_disconnected(monkeypatch):
    from app.api import health
    monkeypatch.setattr(health, "check_db_connection", lambda: {"status": "disconnected"})
    app = FastAPI()
    app.include_router(health.router, prefix="/api")
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 503
        assert response.json()["status"] == "unhealthy"


def test_rapid_transfer_window_is_detected_even_with_older_history(db):
    for i, day in enumerate((1, 10, 20)):
        db.add(OwnershipHistory(history_id=f"RAPID-{i}", survey_number="SYN-101/A", owner_name="Kalyan Varma Dantuluri", transfer_date=date(2026, 1, day), transfer_type="Sale"))
    db.commit()
    save_doc(db)
    assert any(a["type"] == "RAPID_OWNERSHIP_TRANSFER" for a in verification_engine.verify_document("D1", db)["detected_anomalies"])


def test_ml_learns_reference_distribution_and_reports_its_limits(db):
    for i in range(30):
        db.add(LandRecord(record_id=f"ML-{i}", survey_number=f"ML-{i}/A", owner_name="Demo Owner", land_area_acres=0.5 + i * 0.2,
                          village="Demo", mandal="Demo", district="Demo", state="Demo", document_type="Sale"))
    db.commit()
    result = assess_reference_outlier(db, {"record_id": "R1"}, 500)
    assert result["status"] == "ASSESSED"
    assert result["training_records"] == 31
    assert result["model"] == "IsolationForest"
    assert result["outlier_percentile"] >= 90
    assert "not fraud probability" in result["limitation"]
    assert result == assess_reference_outlier(db, {"record_id": "R1"}, 500)


@pytest.mark.parametrize("filename", ["pahani_demo.pdf", "pahani_demo.png"])
def test_actual_pahani_pdf_and_scan_extract_expected_fields(filename):
    result = process_document_ocr(str(ROOT / "sample_data" / filename))
    assert result["status"] == "COMPLETED"
    fields = nlp_engine.extract_information(result["text"])["extracted_fields"]
    assert fields["document_type"] == "Pahani / Adangal"
    assert fields["owner_name"] == "Kalyan Varma Dantuluri"
    assert fields["survey_number"] == "SYN-101/A"
    assert fields["land_area_acres"] == 2.2
    assert fields["khata_number"] == "DEMO-101"
    assert fields["crop_year"] == "2025-2026"


def test_telugu_labelled_text_preserves_owner_and_location():
    fields = nlp_engine.extract_information("పహాణి\nపట్టాదారు పేరు: రామయ్య\nసర్వే నంబరు: 101/A\nగ్రామం: నర్సింగి\nమండలం: గండిపేట\nజిల్లా: రంగారెడ్డి\n")['extracted_fields']
    assert fields["document_type"] == "Pahani / Adangal"
    assert fields["owner_name"] == "రామయ్య"
    assert fields["village"] == "నర్సింగి"
