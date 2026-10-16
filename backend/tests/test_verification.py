import os
import sys
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base
from app.models import LandRecord, OwnershipHistory
from app.verification.engine import LandVerificationEngine


def setup_in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Populate Sample Test Records (matching sample_data test scenarios)
    sample_lands = [
        LandRecord(record_id="REC-1001", owner_name="Anil Kumar Rao", survey_number="101/A", land_area_acres=2.50, village="Greenvalley", mandal="Serilingampally", district="Ranga Reddy", state="Telangana", registration_number="REG-2020-00101", registration_date=date(2020, 3, 15), document_type="Sale Deed"),
        LandRecord(record_id="REC-1006", owner_name="Farhan Ahmed", survey_number="201/A", land_area_acres=5.00, village="Hilltop", mandal="Maheshwaram", district="Ranga Reddy", state="Telangana", registration_number="REG-2018-00615", registration_date=date(2018, 4, 12), document_type="Sale Deed"),
        LandRecord(record_id="REC-1010", owner_name="Jayant Joshi", survey_number="401/A", land_area_acres=1.80, village="Riverside", mandal="Ibrahimpatnam", district="Ranga Reddy", state="Telangana", registration_number="REG-2019-01050", registration_date=date(2019, 2, 28), document_type="Sale Deed"),
        LandRecord(record_id="REC-1012", owner_name="Lokesh Gupta", survey_number="501/A", land_area_acres=4.00, village="Forest Edge", mandal="Moinabad", district="Ranga Reddy", state="Telangana", registration_number="REG-2021-01270", registration_date=date(2021, 10, 15), document_type="Sale Deed"),
        LandRecord(record_id="REC-1013", owner_name="Madhav Singh", survey_number="501/A", land_area_acres=4.00, village="Forest Edge", mandal="Moinabad", district="Ranga Reddy", state="Telangana", registration_number="REG-2023-01380", registration_date=date(2023, 11, 20), document_type="Sale Deed"),
        LandRecord(record_id="REC-1014", owner_name="Nitin Saxena", survey_number="601/A", land_area_acres=2.75, village="Highland", mandal="Chevella", district="Ranga Reddy", state="Telangana", registration_number="REG-2024-01490", registration_date=date(2024, 1, 10), document_type="Sale Deed"),
    ]

    sample_histories = [
        OwnershipHistory(history_id="HIST-001", survey_number="101/A", owner_name="Ramakrishna Rao", transfer_date=date(1995, 4, 10), transfer_type="Original Grant"),
        OwnershipHistory(history_id="HIST-002", survey_number="101/A", owner_name="Anil Kumar Rao", transfer_date=date(2020, 3, 15), transfer_type="Sale Deed"),
        OwnershipHistory(history_id="HIST-015", survey_number="601/A", owner_name="Anand Saxena", transfer_date=date(2023, 12, 1), transfer_type="Original Sale"),
        OwnershipHistory(history_id="HIST-016", survey_number="601/A", owner_name="Vijay Saxena", transfer_date=date(2023, 12, 15), transfer_type="Rapid Resale"),
        OwnershipHistory(history_id="HIST-017", survey_number="601/A", owner_name="Nitin Saxena", transfer_date=date(2024, 1, 10), transfer_type="Rapid Resale"),
    ]

    session.add_all(sample_lands)
    session.add_all(sample_histories)
    session.commit()
    return session


def run_all_verification_tests():
    db = setup_in_memory_db()
    verifier = LandVerificationEngine()

    print("==================================================")
    print("RUNNING VERIFICATION & ANOMALY ENGINE TEST SUITE")
    print("==================================================")

    # Test 1: Clean Matching Record
    print("\n[TEST 1] Clean Matching Record (Survey 101/A, Anil Kumar Rao, 2.50 Acres)...")
    res1 = verifier.verify_extracted_attributes(owner_name="Anil Kumar Rao", survey_number="101/A", land_area=2.50, document_id="DOC-TEST-1", db=db)
    print("Status:", res1["verification_status"])
    print("Anomalies Count:", res1["anomalies_count"])
    assert res1["verification_status"] == "VERIFIED", f"Expected VERIFIED, got {res1['verification_status']}"
    assert res1["anomalies_count"] == 0
    print("[PASS] Test 1 PASSED: Clean match correctly verified!")

    # Test 2: Owner Name Mismatch
    print("\n[TEST 2] Owner Name Mismatch (Survey 201/A, Document: 'Farooq Ahmed' vs Registry: 'Farhan Ahmed')...")
    res2 = verifier.verify_extracted_attributes(owner_name="Farooq Ahmed", survey_number="201/A", land_area=5.00, document_id="DOC-TEST-2", db=db)
    print("Status:", res2["verification_status"])
    anom_types2 = [a["type"] for a in res2["detected_anomalies"]]
    print("Anomalies Detected:", anom_types2)
    assert res2["verification_status"] == "SUSPICIOUS"
    assert "OWNER_NAME_MISMATCH" in anom_types2
    print("[PASS] Test 2 PASSED: Owner name mismatch correctly flagged!")

    # Test 3: Survey Number Mismatch / Not Found
    print("\n[TEST 3] Unregistered Survey Number (Survey 999/Z)...")
    res3 = verifier.verify_extracted_attributes(owner_name="John Doe", survey_number="999/Z", land_area=3.00, document_id="DOC-TEST-3", db=db)
    print("Status:", res3["verification_status"])
    anom_types3 = [a["type"] for a in res3["detected_anomalies"]]
    print("Anomalies Detected:", anom_types3)
    assert res3["verification_status"] in ["SUSPICIOUS", "REFERENCE_NOT_FOUND"]
    assert "SURVEY_NOT_FOUND" in anom_types3
    print("[PASS] Test 3 PASSED: Unregistered survey correctly flagged!")

    # Test 4: Land Area Mismatch (Survey 401/A, Claimed: 2.90 Acres vs Registry: 1.80 Acres)
    print("\n[TEST 4] Land Area Inflation Discrepancy (Survey 401/A, Claimed: 2.90 Acres vs Registry: 1.80 Acres)...")
    res4 = verifier.verify_extracted_attributes(owner_name="Jayant Joshi", survey_number="401/A", land_area=2.90, document_id="DOC-TEST-4", db=db)
    print("Status:", res4["verification_status"])
    anom_types4 = [a["type"] for a in res4["detected_anomalies"]]
    print("Anomalies Detected:", anom_types4)
    assert res4["verification_status"] == "SUSPICIOUS"
    assert "LAND_AREA_MISMATCH" in anom_types4
    print("[PASS] Test 4 PASSED: Land area discrepancy correctly detected!")

    # Test 5: Duplicate Registration / Double Selling Alert (Survey 501/A)
    print("\n[TEST 5] Duplicate Registration Fraud (Survey 501/A registered under Lokesh Gupta and Madhav Singh)...")
    res5 = verifier.verify_extracted_attributes(owner_name="Lokesh Gupta", survey_number="501/A", land_area=4.00, document_id="DOC-TEST-5", db=db)
    print("Status:", res5["verification_status"])
    anom_types5 = [a["type"] for a in res5["detected_anomalies"]]
    print("Anomalies Detected:", anom_types5)
    assert "DUPLICATE_REGISTRATION_FLAGGED" in anom_types5
    print("[PASS] Test 5 PASSED: Duplicate registration fraud alert triggered!")

    # Test 6: Rapid Ownership Transfer Anomaly (Survey 601/A - 3 transfers in 30 days)
    print("\n[TEST 6] Rapid Ownership Transfer Anomaly (Survey 601/A)...")
    res6 = verifier.verify_extracted_attributes(owner_name="Nitin Saxena", survey_number="601/A", land_area=2.75, document_id="DOC-TEST-6", db=db)
    print("Status:", res6["verification_status"])
    anom_types6 = [a["type"] for a in res6["detected_anomalies"]]
    print("Anomalies Detected:", anom_types6)
    assert "RAPID_OWNERSHIP_TRANSFER" in anom_types6
    print("[PASS] Test 6 PASSED: Rapid ownership transfer anomaly detected!")

    # Test 7: Incomplete Document Record (Missing Survey & Zero Area)
    print("\n[TEST 7] Incomplete Document Record...")
    res7 = verifier.verify_extracted_attributes(owner_name="Unknown Owner", survey_number="", land_area=0.0, document_id="DOC-TEST-7", db=db)
    print("Status:", res7["verification_status"])
    anom_types7 = [a["type"] for a in res7["detected_anomalies"]]
    print("Anomalies Detected:", anom_types7)
    assert res7["verification_status"] == "UNVERIFIED"
    assert "INCOMPLETE_DOCUMENT_DATA" in anom_types7
    print("[PASS] Test 7 PASSED: Incomplete document data correctly handled!")

    print("\n==================================================")
    print("ALL 7 VERIFICATION & ANOMALY TESTS PASSED!")
    print("==================================================")


def test_verification_suite():
    run_all_verification_tests()


if __name__ == "__main__":
    run_all_verification_tests()
