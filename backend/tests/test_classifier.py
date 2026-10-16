import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.nlp.classifier import document_classifier
from app.nlp.extractor import nlp_engine


def test_classify_sale_deed():
    text = """
    REGISTERED SALE DEED
    This Deed of Absolute Sale executed between Vendor Mr. Rajesh Kumar and Vendee Mr. Suresh Patel.
    Total Consideration Amount: Rs. 45,00,000/-. Absolute owner transfer.
    """
    res = document_classifier.classify_document(text)
    assert res["document_type"] == "Sale Deed"
    assert res["is_confident"] is True


def test_classify_encumbrance_certificate():
    text = """
    REGISTRATION AND STAMPS DEPARTMENT
    STATEMENT OF ENCUMBRANCE ON PROPERTY
    FORM NO. 15
    Certified that Nil Encumbrance transactions were found for the search period 01-Jan-2010 to 31-Dec-2025.
    """
    res = document_classifier.classify_document(text)
    assert res["document_type"] == "Encumbrance Certificate"
    assert res["is_confident"] is True


def test_classify_patta_passbook():
    text = """
    GOVERNMENT OF TELANGANA - REVENUE DEPARTMENT
    RECORD OF RIGHTS - ROR 1B / PATTA PASSBOOK
    Pattadar Name: Venkata Ramanappa
    Khata No: 402, Ryotwari Patta
    """
    res = document_classifier.classify_document(text)
    assert res["document_type"] == "Patta Passbook / RoR"
    assert res["is_confident"] is True


def test_nlp_extraction_with_units_and_parties():
    deed_text = """
    DEED OF SALE
    EXECUTANT (SELLER): Kiran Verma
    PURCHASER (BUYER): Arun Kumar
    SURVEY NO: 104/2
    CLAIMED EXTENT: 240 square yards
    VILLAGE: Green Valley
    DISTRICT: Demo District
    DOCUMENT NO: DOC-2026-991
    DATE: 15 September 2026
    """
    res = nlp_engine.extract_information(deed_text)
    assert res["status"] == "SUCCESS"
    assert res["document_type"] == "Sale Deed"
    fields = res["extracted_fields"]

    assert fields["owner_name"] in ["Kiran Verma", "Arun Kumar"]
    assert fields["buyer_name"] == "Arun Kumar"
    assert fields["survey_number"] == "104/2"
    assert fields["subdivision_number"] == "2"
    assert fields["land_area_raw"] == "240 square yards"
    assert fields["land_area_unit"] == "square yards"
    assert fields["land_area_numeric"] == 240.0
    # Verified conversion: 240 / 4840 = 0.0496
    assert fields["land_area_normalized_acres"] == 0.0496
    assert fields["village"] == "Green Valley"
    assert fields["district"] == "Demo District"
    assert fields["registration_number"] == "DOC-2026-991"
    assert fields["registration_date"] == "15 September 2026"
