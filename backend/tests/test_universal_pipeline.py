import os
import sys
import io
import asyncio
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from PIL import Image, ImageDraw, ImageFont

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base
from app.models import LandRecord, OwnershipHistory, DocumentRecord
from app.ocr.processor import process_document_ocr
from app.nlp.extractor import nlp_engine
from app.nlp.classifier import classify_document_type
from app.nlp.unit_converter import normalize_land_area, compare_areas
from app.verification.engine import LandVerificationEngine
from app.risk_scoring.engine import ExplainableRiskScoringEngine
from app.api.documents import upload_document, get_document_details
from fastapi import UploadFile


def create_synthetic_multipage_pdf(file_path: str):
    """Creates a 2-page synthetic PDF for multipage pipeline testing."""
    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font = ImageFont.load_default()

    # Page 1: Deed overview and parties
    img1 = Image.new("RGB", (900, 1100), color=(255, 255, 255))
    draw1 = ImageDraw.Draw(img1)
    draw1.text((50, 50), "GOVERNMENT OF TELANGANA\nREGISTRATION AND STAMPS DEPARTMENT\n\nSALE DEED FOR AGRICULTURAL LAND\nDOCUMENT NUMBER: DOC-MULTI-2026-099\nDATE OF REGISTRATION: 16-OCT-2026\n\nEXECUTANT / VENDOR: Devi Prasad Sharma\nCLAIMANT / PURCHASER: Naveen Reddy\n", fill=(0, 0, 0), font=font)

    # Page 2: Schedule of Property and boundaries
    img2 = Image.new("RGB", (900, 1100), color=(255, 255, 255))
    draw2 = ImageDraw.Draw(img2)
    draw2.text((50, 50), "SCHEDULE OF PROPERTY\n\nSURVEY NUMBER: SYN-102/B\nSUB-DIVISION: B\nTOTAL EXTENT: 1.50 ACRES\nVILLAGE: Narsingi\nMANDAL: Gandipet\nDISTRICT: Ranga Reddy\nSTATE: Telangana\n\nBOUNDARIES:\nNORTH: Road\nSOUTH: Stream\nEAST: Plot 101\nWEST: Open Land\n", fill=(0, 0, 0), font=font)

    img1.save(file_path, "PDF", save_all=True, append_images=[img2])


def test_multipage_pdf_processing():
    """Validates that multipage PDFs are tracked page-by-page and all fields extracted."""
    test_pdf = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_temp_multipage.pdf"))
    create_synthetic_multipage_pdf(test_pdf)

    try:
        ocr_res = process_document_ocr(test_pdf)
        assert ocr_res["status"] == "COMPLETED"
        assert ocr_res["pages_count"] >= 2
        assert len(ocr_res["pages"]) >= 2
        assert ocr_res["pages"][0]["page_number"] == 1
        assert ocr_res["pages"][1]["page_number"] == 2

        # Verify OCR combined text covers both pages
        full_text = ocr_res["text"]
        assert "Devi Prasad Sharma" in full_text
        assert "SYN-102/B" in full_text
        assert "1.50 ACRES" in full_text

        # NLP extraction
        nlp_res = nlp_engine.extract_information(full_text, pages_metadata=ocr_res["pages"])
        assert nlp_res["status"] == "SUCCESS"
        fields = nlp_res["extracted_fields"]
        assert fields["survey_number"] == "SYN-102/B"
        assert fields["land_area_acres"] == 1.50
        assert fields["village"] == "Narsingi"
        assert fields["mandal"] == "Gandipet"
        assert fields["district"] == "Ranga Reddy"
        assert fields["registration_number"] == "DOC-MULTI-2026-099"

        # Check field metadata tracks page occurrence
        meta = nlp_res["field_metadata"]
        assert "survey_number" in meta
        assert meta["survey_number"]["confidence"] >= 0.8
    finally:
        if os.path.exists(test_pdf):
            os.remove(test_pdf)


def test_image_ocr_with_preprocessor():
    """Validates image formats (PNG & JPG) with deskewing and contrast preprocessing."""
    sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sample_data"))
    img_files = ["ocr_test_synthetic_deed.png", "ocr_test_synthetic_deed.jpg"]

    for img_name in img_files:
        img_path = os.path.join(sample_dir, img_name)
        if not os.path.exists(img_path):
            continue

        ocr_res = process_document_ocr(img_path)
        assert ocr_res["status"] == "COMPLETED"
        assert "Tesseract" in ocr_res["engine"]
        assert ocr_res["confidence"] > 80.0
        assert "Kalyan Varma Dantuluri" in ocr_res["text"]
        assert "SYN-101/A" in ocr_res["text"]

        nlp_res = nlp_engine.extract_information(ocr_res["text"])
        fields = nlp_res["extracted_fields"]
        assert fields["owner_name"] == "Kalyan Varma Dantuluri"
        assert fields["survey_number"] == "SYN-101/A"
        assert fields["land_area_acres"] == 2.20
        assert fields["village"] == "Narsingi"


def test_encumbrance_certificate_classification_and_extraction():
    """Validates specialized document classifier & extraction for Encumbrance Certificates."""
    ec_text = (
        "GOVERNMENT OF TELANGANA - REGISTRATION AND STAMPS DEPARTMENT\n"
        "STATEMENT OF ENCUMBRANCE ON PROPERTY (FORM NO. 32)\n"
        "Certificate No: EC-2026-8812\n"
        "Application Number: APP-7712\n"
        "Search Period: 01-Jan-2010 to 15-Oct-2026\n"
        "Owner / Title Holder: Smt. Anuradha Rao\n"
        "Survey Number: 304/C\n"
        "Extent: 3.50 Acres\n"
        "Village: Kondapur, Mandal: Serilingampally, District: Ranga Reddy\n"
        "Encumbrance Status: NIL ENCUMBRANCE (Nil certificate issued)\n"
    )

    doc_class = classify_document_type(ec_text)
    assert doc_class["document_type"] == "Encumbrance Certificate"
    assert doc_class["classification_confidence"] >= 75.0

    nlp_res = nlp_engine.extract_information(ec_text)
    assert nlp_res["document_type"] == "Encumbrance Certificate"
    fields = nlp_res["extracted_fields"]
    assert fields["owner_name"] == "Anuradha Rao"
    assert fields["survey_number"] == "304/C"
    assert fields["land_area_acres"] == 3.50
    assert fields["encumbrance_status"] in ["Nil Encumbrance", "NIL ENCUMBRANCE"]


def test_patta_passbook_classification_and_extraction():
    """Validates document classifier for Patta Passbooks / Record of Rights."""
    patta_text = (
        "TELANGANA LAND REVENUE ADMINISTRATION - DHARANI PORTAL\n"
        "PATTADAR PASSBOOK CUM TITLE DEED\n"
        "ROR 1-B NAMUNA EXTRACT\n"
        "Passbook Number: T19050012345\n"
        "Pattadar Name: Venkat Swamy Goud\n"
        "Father's Name: Mallaiah Goud\n"
        "Survey Number: 118/A\n"
        "Total Extent: 20 Guntas\n"
        "Khata Number: KH-409\n"
        "Village: Gachibowli, Mandal: Serilingampally, District: Ranga Reddy\n"
    )

    doc_class = classify_document_type(patta_text)
    assert doc_class["document_type"] == "Patta Passbook / RoR"
    assert doc_class["classification_confidence"] >= 75.0

    nlp_res = nlp_engine.extract_information(patta_text)
    fields = nlp_res["extracted_fields"]
    assert fields["owner_name"] == "Venkat Swamy Goud"
    assert fields["survey_number"] == "118/A"
    # 20 Guntas normalized to Acres = 20 / 40 = 0.50 Acres
    assert fields["land_area_raw"] == "20 Guntas"
    assert fields["land_area_normalized_acres"] == 0.50
    assert abs(fields["land_area_acres"] - 0.50) < 1e-4


def test_area_normalization_in_verification():
    """Ensures square yards, guntas, and acres are verified mathematically without false mismatch."""
    db_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=db_engine)
    Session = sessionmaker(bind=db_engine)
    db = Session()

    # Seed reference parcel with 0.0496 Acres (equivalent to 240 sq yds)
    ref1 = LandRecord(
        record_id="REC-TEST-240",
        owner_name="Arun Kumar",
        survey_number="SY-TEST-104/2",
        land_area_acres=0.0496,
        village="Green Valley",
        mandal="Demo Mandal",
        district="Demo District",
        state="Telangana",
        registration_number="DOC-TEST-2026-001",
        registration_date=date(2026, 9, 15),
        document_type="Sale Deed"
    )
    db.add(ref1)
    db.commit()

    verifier = LandVerificationEngine()

    # Document claiming 240 square yards against reference of 0.0496 Acres should MATCH!
    res_match = verifier.verify_extracted_attributes(
        owner_name="Arun Kumar",
        survey_number="SY-TEST-104/2",
        land_area=240.0,
        land_area_unit="square yards",
        land_area_raw="240 square yards",
        document_id="DOC-TEST-SY-MATCH",
        db=db
    )
    assert res_match["field_matches"]["land_area_match"] is True

    # Conversely, if document claimed 240 Acres against 0.0496 Acres, it must DISCREPANCY
    res_mismatch = verifier.verify_extracted_attributes(
        owner_name="Arun Kumar",
        survey_number="SY-TEST-104/2",
        land_area=240.0,
        land_area_unit="Acres",
        land_area_raw="240 Acres",
        document_id="DOC-TEST-SY-MISMATCH",
        db=db
    )
    assert res_mismatch["field_matches"]["land_area_match"] is False
    assert any(a["type"] == "LAND_AREA_MISMATCH" for a in res_mismatch["detected_anomalies"])


def test_unindexed_survey_responsible_verification():
    """
    Validates that a document with an unindexed survey is reported as REFERENCE_NOT_FOUND
    and receives 0 fraud penalty points in the risk scoring engine.
    """
    db_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=db_engine)
    Session = sessionmaker(bind=db_engine)
    db = Session()

    # Document with non-existent survey parcel
    doc = DocumentRecord(
        document_id="DOC-UNINDEXED-001",
        filename="Unindexed_Survey.pdf",
        file_path="uploads/unindexed.pdf",
        file_type="PDF",
        file_size_bytes=1024,
        extracted_owner_name="Naveen Fictional Owner",
        extracted_survey_number="UNINDEXED-9999/Z",
        extracted_land_area=3.5,
        extracted_text="Document for Naveen Fictional Owner Survey UNINDEXED-9999/Z 3.5 Acres"
    )
    db.add(doc)
    db.commit()

    verifier = LandVerificationEngine()
    ver_res = verifier.verify_document("DOC-UNINDEXED-001", db=db)

    assert ver_res["verification_status"] == "REFERENCE_NOT_FOUND"
    assert ver_res["reference_status"] == "NO_MATCHING_REFERENCE"

    # Risk scoring verification: 0 fraud penalty points!
    risk_scorer = ExplainableRiskScoringEngine()
    risk_res = risk_scorer.compute_risk_assessment("DOC-UNINDEXED-001", db=db)

    assert risk_res["risk_score"] == 0
    assert risk_res["risk_level"] == "LOW"
    assert "Unindexed parcel in demonstration registry" in risk_res["recommendation"] or "No major inconsistency detected" in risk_res["recommendation"]


def test_upload_file_isolation_and_no_stale_data():
    """Validates that consecutive uploads are isolated and never report hardcoded fallback data."""
    db_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=db_engine)
    Session = sessionmaker(bind=db_engine)
    db = Session()

    sample_pdf = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "LandGuard_Synthetic_Test_Land_Record.pdf"))
    with open(sample_pdf, "rb") as f:
        pdf_bytes = f.read()

    up = UploadFile(filename="LandGuard_Synthetic_Test_Land_Record.pdf", file=io.BytesIO(pdf_bytes))
    data = asyncio.run(upload_document(file=up, db=db))

    doc_id = data.get("document_id")
    assert doc_id is not None

    details = get_document_details(doc_id, db=db)
    # Must contain extracted values from PDF
    assert details["extracted_owner_name"] == "Arun Kumar"
    assert details["extracted_survey_number"] == "SY-TEST-104/2"

    # Must NEVER contain hardcoded legacy fallback values
    assert details["extracted_owner_name"] != "Rajesh Kumar Sharma"
    assert details["extracted_survey_number"] != "402/B"
    assert "Rajesh Kumar Sharma" not in details["extracted_text"]
    assert "402/B" not in details["extracted_text"]
