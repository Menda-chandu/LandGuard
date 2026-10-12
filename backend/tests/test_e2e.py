import os
import sys
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base
from app.models import LandRecord, OwnershipHistory, DocumentRecord
from app.ocr.processor import process_document_ocr
from app.nlp.extractor import nlp_engine
from app.verification.engine import verification_engine
from app.risk_scoring.engine import risk_scoring_engine
from app.gis.spatial_engine import gis_spatial_engine


def setup_test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed baseline DB records
    land1 = LandRecord(record_id="REC-1011", owner_name="Kiran Mazumdar", survey_number="402/B", land_area_acres=2.00, village="Riverside", mandal="Ibrahimpatnam", district="Ranga Reddy", state="Telangana", registration_number="REG-2023-01160", registration_date=date(2023, 4, 10), document_type="Sale Deed")
    hist1 = OwnershipHistory(history_id="HIST-011", survey_number="402/B", owner_name="Subhash Mazumdar", transfer_date=date(2005, 7, 14), transfer_type="Original Grant")
    hist2 = OwnershipHistory(history_id="HIST-012", survey_number="402/B", owner_name="Kiran Mazumdar", transfer_date=date(2023, 4, 10), transfer_type="Sale Deed")

    session.add_all([land1, hist1, hist2])
    session.commit()
    return session


def run_e2e_pipeline_test():
    print("==================================================")
    print("RUNNING LANDGUARD END-TO-END INTEGRATION TEST")
    print("==================================================")

    db = setup_test_db()

    # Step 1: Upload & OCR Ingestion
    sample_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "sample_deed.png"))
    print("\n[STEP 1] Running OCR Ingestion on sample_deed.png...")
    ocr_res = process_document_ocr(sample_img)
    ocr_text = ocr_res.get("text", "")
    print("OCR Engine:", ocr_res.get("engine"))
    print("OCR Confidence:", ocr_res.get("confidence"), "%")
    assert len(ocr_text) > 50, "OCR text extraction failed"

    # Step 2: NLP Information Extraction
    print("\n[STEP 2] Running NLP Entity Extraction...")
    nlp_res = nlp_engine.extract_information(ocr_text)
    fields = nlp_res.get("extracted_fields", {})
    print("Owner Name Extracted:", fields.get("owner_name"))
    print("Survey Number Extracted:", fields.get("survey_number"))
    print("Land Area Extracted:", fields.get("land_area_acres"), "Acres")
    print("Location Summary:", nlp_res.get("location_summary"))
    assert fields.get("owner_name") == "Rajesh Kumar Sharma"
    assert fields.get("survey_number") == "402/B"
    assert fields.get("land_area_acres") == 2.45

    # Persist Document Record in DB
    doc = DocumentRecord(
        document_id="DOC-E2E-TEST",
        filename="sample_deed.png",
        file_path="sample_data/sample_deed.png",
        file_type="PNG",
        file_size_bytes=142850,
        ocr_status=ocr_res.get("status"),
        extracted_text=ocr_text,
        extracted_owner_name=fields.get("owner_name"),
        extracted_survey_number=fields.get("survey_number"),
        extracted_land_area=fields.get("land_area_acres"),
        extracted_location=nlp_res.get("location_summary"),
        ocr_confidence_score=ocr_res.get("confidence")
    )
    db.add(doc)
    db.commit()

    # Step 3: Verification & Anomaly Detection
    print("\n[STEP 3] Running Verification & Anomaly Detection Engine...")
    ver_res = verification_engine.verify_document("DOC-E2E-TEST", db)
    print("Verification Status:", ver_res.get("verification_status"))
    print("Matched Land Record ID:", ver_res.get("matched_record_id"))
    print("Anomalies Count:", ver_res.get("anomalies_count"))
    for anom in ver_res.get("detected_anomalies", []):
        print(f"  - [{anom['severity']}] {anom['title']}: {anom['description']}")
    assert ver_res.get("verification_status") == "SUSPICIOUS"
    assert ver_res.get("anomalies_count") >= 2

    # Step 4: Explainable Risk Scoring Engine
    print("\n[STEP 4] Running Explainable Risk Scoring Engine...")
    risk_res = risk_scoring_engine.compute_risk_assessment("DOC-E2E-TEST", db)
    print("Risk Score:", risk_res.get("risk_score"), "/ 100")
    print("Risk Level:", risk_res.get("risk_level"))
    print("Recommendation:", risk_res.get("recommendation"))
    assert risk_res.get("risk_score") >= 60
    assert risk_res.get("risk_level") in ["HIGH", "CRITICAL"]

    # Step 5: GIS Spatial Verification Engine
    print("\n[STEP 5] Running GIS Spatial Mapping & CAD Polygon Verification...")
    gis_res = gis_spatial_engine.verify_spatial_location(
        survey_number=fields.get("survey_number"),
        doc_village=fields.get("village"),
        doc_district=fields.get("district"),
        db=db
    )
    print("GIS Spatial Match:", gis_res.get("spatial_match"))
    print("GIS Parcel Polygon Found:", gis_res.get("parcel_found"))
    assert gis_res.get("parcel_found") == True

    print("\n==================================================")
    print("[SUCCESS] FULL E2E PIPELINE (OCR -> NLP -> VERIFY -> RISK -> GIS) PASSED!")
    print("==================================================")


def test_e2e_pipeline():
    run_e2e_pipeline_test()


if __name__ == "__main__":
    run_e2e_pipeline_test()
