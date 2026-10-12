import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.nlp.extractor import nlp_engine
from app.ocr.processor import process_document_ocr


def test_sample_deed_nlp_extraction():
    print("==================================================")
    print("TEST 1: Extracting NLP Entities from sample_deed.png")
    print("==================================================")

    sample_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "sample_deed.png"))
    ocr_result = process_document_ocr(sample_image_path)
    ocr_text = ocr_result.get("text", "")

    nlp_res = nlp_engine.extract_information(ocr_text)

    print("NLP Status:", nlp_res.get("status"))
    print("NLP Confidence Score:", nlp_res.get("nlp_confidence_score"), "%")
    print("Location Summary:", nlp_res.get("location_summary"))
    print("Extracted Attributes:")
    for k, v in nlp_res.get("extracted_fields", {}).items():
        print(f"  - {k}: {v}")

    fields = nlp_res.get("extracted_fields", {})
    assert fields.get("owner_name") in ["Rajesh Kumar Sharma", "Rajosh Kumar Sharma"], f"Expected Rajesh/Rajosh Kumar Sharma, got {fields.get('owner_name')}"
    assert fields.get("survey_number") in ["402/B", "402/8"], f"Expected 402/B or 402/8, got {fields.get('survey_number')}"
    assert fields.get("land_area_acres") == 2.45, f"Expected 2.45, got {fields.get('land_area_acres')}"
    print("\n[PASS] Test 1 PASSED: All key fields extracted correctly from sample_deed.png!")


def test_variations_nlp_extraction():
    print("\n==================================================")
    print("TEST 2: Testing OCR Variations & Missing Fields")
    print("==================================================")

    faint_ocr_text = """
    REGISTERED GIFT DEED
    TITLE HOLDER: Chandra Shekhar Verma
    SY NO: 103/C
    TOTAL AREA: 4.20 ACRES
    VILLAGE: Sunnyside
    MANDAL: Rajendranagar
    DISTRICT: Ranga Reddy
    STATE: Telangana
    REG NO: REG-2019-00305
    DATE: 2019-11-10
    NORTH: Survey 102/B
    SOUTH: Main Village Road
    EAST: Forest Boundary
    WEST: Open Agricultural Land
    """

    res = nlp_engine.extract_information(faint_ocr_text)
    fields = res.get("extracted_fields", {})
    boundaries = fields.get("boundary_details", {})

    print("Extracted Document Type:", fields.get("document_type"))
    print("Owner Name:", fields.get("owner_name"))
    print("Survey Number:", fields.get("survey_number"))
    print("Land Area:", fields.get("land_area_acres"), "Acres")
    print("Boundaries:", boundaries)

    assert fields.get("document_type") == "Gift Deed"
    assert fields.get("owner_name") == "Chandra Shekhar Verma"
    assert fields.get("survey_number") == "103/C"
    assert fields.get("land_area_acres") == 4.20
    assert boundaries.get("north") == "Survey 102/B"
    print("\n[PASS] Test 2 PASSED: Boundary parsing and deed type extraction succeeded!")


if __name__ == "__main__":
    test_sample_deed_nlp_extraction()
    test_variations_nlp_extraction()
