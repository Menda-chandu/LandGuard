import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.gis.spatial_engine import gis_spatial_engine


def run_all_gis_tests():
    print("==================================================")
    print("RUNNING GIS SPATIAL ENGINE TEST SUITE")
    print("==================================================")

    # Test 1: Matching Parcel (Survey 101/A in Greenvalley, Ranga Reddy)
    print("\n[TEST 1] Testing Matching Parcel (Survey 101/A)...")
    res1 = gis_spatial_engine.verify_spatial_location(
        survey_number="101/A",
        doc_village="Greenvalley",
        doc_district="Ranga Reddy"
    )
    print("Spatial Match:", res1["spatial_match"])
    print("Parcel Found:", res1["parcel_found"])
    print("GIS Village:", res1["gis_properties"]["village"])
    assert res1["spatial_match"] == True, f"Expected spatial_match True, got {res1['spatial_match']}"
    assert res1["parcel_found"] == True
    assert len(res1["anomalies"]) == 0
    print("[PASS] Test 1 PASSED: Matching parcel verified successfully!")

    # Test 2: Mismatched Parcel Location (Survey 101/A claimed in Village "Sunnyside")
    print("\n[TEST 2] Testing Location Mismatched Parcel (Survey 101/A claimed in Sunnyside vs GIS Greenvalley)...")
    res2 = gis_spatial_engine.verify_spatial_location(
        survey_number="101/A",
        doc_village="Sunnyside",
        doc_district="Ranga Reddy"
    )
    print("Spatial Match:", res2["spatial_match"])
    anom_types2 = [a["type"] for a in res2["anomalies"]]
    print("Detected Anomalies:", anom_types2)
    assert res2["spatial_match"] == False
    assert "SPATIAL_LOCATION_MISMATCH" in anom_types2
    print("[PASS] Test 2 PASSED: Location mismatch correctly flagged!")

    # Test 3: Missing Parcel (Survey 999/Z not in GeoJSON)
    print("\n[TEST 3] Testing Missing GIS Parcel (Survey 999/Z)...")
    res3 = gis_spatial_engine.verify_spatial_location(
        survey_number="999/Z",
        doc_village="Greenvalley"
    )
    print("Spatial Match:", res3["spatial_match"])
    print("Parcel Found:", res3["parcel_found"])
    anom_types3 = [a["type"] for a in res3["anomalies"]]
    print("Detected Anomalies:", anom_types3)
    assert res3["spatial_match"] == False
    assert res3["parcel_found"] == False
    assert "GIS_PARCEL_NOT_FOUND" in anom_types3
    print("[PASS] Test 3 PASSED: Missing parcel correctly handled!")

    print("\n==================================================")
    print("ALL GIS SPATIAL TESTS (MATCH, MISMATCH, MISSING) PASSED!")
    print("==================================================")


def test_gis_suite():
    run_all_gis_tests()


if __name__ == "__main__":
    run_all_gis_tests()
