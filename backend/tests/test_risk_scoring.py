import os
import sys
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base
from app.models import LandRecord, OwnershipHistory, DocumentRecord
from app.risk_scoring.engine import ExplainableRiskScoringEngine


def setup_in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Base test records
    lands = [
        LandRecord(record_id="REC-1001", owner_name="Anil Kumar Rao", survey_number="101/A", land_area_acres=2.50, village="Greenvalley", mandal="Serilingampally", district="Ranga Reddy", state="Telangana", registration_number="REG-2020-00101", registration_date=date(2020, 3, 15), document_type="Sale Deed"),
        LandRecord(record_id="REC-1006", owner_name="Farhan Ahmed", survey_number="201/A", land_area_acres=5.00, village="Hilltop", mandal="Maheshwaram", district="Ranga Reddy", state="Telangana", registration_number="REG-2018-00615", registration_date=date(2018, 4, 12), document_type="Sale Deed"),
        LandRecord(record_id="REC-1010", owner_name="Jayant Joshi", survey_number="401/A", land_area_acres=1.80, village="Riverside", mandal="Ibrahimpatnam", district="Ranga Reddy", state="Telangana", registration_number="REG-2019-01050", registration_date=date(2019, 2, 28), document_type="Sale Deed"),
        LandRecord(record_id="REC-1012", owner_name="Lokesh Gupta", survey_number="501/A", land_area_acres=4.00, village="Forest Edge", mandal="Moinabad", district="Ranga Reddy", state="Telangana", registration_number="REG-2021-01270", registration_date=date(2021, 10, 15), document_type="Sale Deed"),
        LandRecord(record_id="REC-1013", owner_name="Madhav Singh", survey_number="501/A", land_area_acres=4.00, village="Forest Edge", mandal="Moinabad", district="Ranga Reddy", state="Telangana", registration_number="REG-2023-01380", registration_date=date(2023, 11, 20), document_type="Sale Deed"),
    ]

    histories = [
        OwnershipHistory(history_id="HIST-001", survey_number="101/A", owner_name="Ramakrishna Rao", transfer_date=date(1995, 4, 10), transfer_type="Original Grant"),
        OwnershipHistory(history_id="HIST-002", survey_number="101/A", owner_name="Anil Kumar Rao", transfer_date=date(2020, 3, 15), transfer_type="Sale Deed"),
        OwnershipHistory(history_id="HIST-015", survey_number="601/A", owner_name="Anand Saxena", transfer_date=date(2023, 12, 1), transfer_type="Original Sale"),
        OwnershipHistory(history_id="HIST-016", survey_number="601/A", owner_name="Vijay Saxena", transfer_date=date(2023, 12, 15), transfer_type="Rapid Resale"),
        OwnershipHistory(history_id="HIST-017", survey_number="601/A", owner_name="Nitin Saxena", transfer_date=date(2024, 1, 10), transfer_type="Rapid Resale"),
    ]

    session.add_all(lands)
    session.add_all(histories)
    session.commit()
    return session


def run_all_risk_scoring_tests():
    db = setup_in_memory_db()
    risk_engine = ExplainableRiskScoringEngine()

    print("==================================================")
    print("RUNNING EXPLAINABLE RISK SCORING ENGINE TEST SUITE")
    print("==================================================")

    # 1. LOW Risk Scenario (0-29 Score)
    print("\n[TEST 1] Testing LOW Risk Scenario (Clean record 101/A)...")
    doc1 = DocumentRecord(document_id="DOC-LOW-1", filename="Clean_Deed.pdf", file_path="uploads/clean.pdf", file_type="PDF", file_size_bytes=1000, extracted_owner_name="Anil Kumar Rao", extracted_survey_number="101/A", extracted_land_area=2.50, extracted_text="Deed for Anil Kumar Rao Survey 101/A 2.50 Acres")
    db.add(doc1)
    db.commit()

    res1 = risk_engine.compute_risk_assessment("DOC-LOW-1", db)
    print(f"Risk Score: {res1['risk_score']} | Level: {res1['risk_level']} | Recommendation: {res1['recommendation']}")
    assert res1['risk_level'] == "LOW", f"Expected LOW, got {res1['risk_level']}"
    assert res1['risk_score'] < 30
    assert res1['recommendation'] == "No major inconsistency detected"
    print("[PASS] LOW Risk test passed successfully!")

    # 2. MEDIUM Risk Scenario (30-59 Score)
    print("\n[TEST 2] Testing MEDIUM Risk Scenario (Land Area Mismatch 20 pts + History Chain 15 pts = 35 pts)...")
    doc2 = DocumentRecord(document_id="DOC-MED-1", filename="Area_Mismatch.pdf", file_path="uploads/area.pdf", file_type="PDF", file_size_bytes=1000, extracted_owner_name="Jayant Joshi", extracted_survey_number="401/A", extracted_land_area=2.90, extracted_text="Deed for Jayant Joshi Survey 401/A 2.90 Acres")
    db.add(doc2)
    db.commit()

    res2 = risk_engine.compute_risk_assessment("DOC-MED-1", db)
    print(f"Risk Score: {res2['risk_score']} | Level: {res2['risk_level']} | Recommendation: {res2['recommendation']}")
    assert res2['risk_level'] == "MEDIUM", f"Expected MEDIUM, got {res2['risk_level']}"
    assert 30 <= res2['risk_score'] <= 59
    assert res2['recommendation'] == "Manual review recommended"
    print("[PASS] MEDIUM Risk test passed successfully!")

    # 3. HIGH Risk Scenario (60-79 Score)
    print("\n[TEST 3] Testing HIGH Risk Scenario (Owner Mismatch 25 pts + Area Mismatch 20 pts + History Chain 15 pts = 60 pts)...")
    doc3 = DocumentRecord(document_id="DOC-HIGH-1", filename="High_Risk.pdf", file_path="uploads/high.pdf", file_type="PDF", file_size_bytes=1000, extracted_owner_name="Farooq Ahmed", extracted_survey_number="201/A", extracted_land_area=6.50, extracted_text="Deed for Farooq Ahmed Survey 201/A 6.50 Acres")
    db.add(doc3)
    db.commit()

    res3 = risk_engine.compute_risk_assessment("DOC-HIGH-1", db)
    print(f"Risk Score: {res3['risk_score']} | Level: {res3['risk_level']} | Recommendation: {res3['recommendation']}")
    assert res3['risk_level'] == "HIGH", f"Expected HIGH, got {res3['risk_level']}"
    assert 60 <= res3['risk_score'] <= 79
    assert res3['recommendation'] == "Further verification required"
    print("[PASS] HIGH Risk test passed successfully!")

    # 4. CRITICAL Risk Scenario (80-100 Score)
    print("\n[TEST 4] Testing CRITICAL Risk Scenario (Duplicate Reg 30 pts + Owner Mismatch 25 pts + Area Mismatch 20 pts + History 15 pts = 90 pts)...")
    doc4 = DocumentRecord(document_id="DOC-CRIT-1", filename="Critical_Fraud.pdf", file_path="uploads/crit.pdf", file_type="PDF", file_size_bytes=1000, extracted_owner_name="Unknown Seller", extracted_survey_number="501/A", extracted_land_area=5.50, extracted_text="Deed for Unknown Seller Survey 501/A 5.50 Acres")
    db.add(doc4)
    db.commit()

    res4 = risk_engine.compute_risk_assessment("DOC-CRIT-1", db)
    print(f"Risk Score: {res4['risk_score']} | Level: {res4['risk_level']} | Recommendation: {res4['recommendation']}")
    assert res4['risk_level'] == "CRITICAL", f"Expected CRITICAL, got {res4['risk_level']}"
    assert res4['risk_score'] >= 80
    assert res4['recommendation'] == "Immediate detailed verification required"
    print("[PASS] CRITICAL Risk test passed successfully!")

    print("\n==================================================")
    print("ALL RISK SCORING TESTS (LOW, MED, HIGH, CRIT) PASSED!")
    print("==================================================")


def test_risk_scoring_suite():
    run_all_risk_scoring_tests()


if __name__ == "__main__":
    run_all_risk_scoring_tests()
