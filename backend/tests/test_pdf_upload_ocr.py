import os
import sys
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base, get_db
from app.models import DocumentRecord
from app.ocr.processor import process_document_ocr
from app.nlp.extractor import nlp_engine
import asyncio
import io
from fastapi import UploadFile
from app.api.documents import upload_document, get_document_details

def test_synthetic_pdf_ocr_and_nlp_extraction():
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'sample_data', 'LandGuard_Synthetic_Test_Land_Record.pdf'))
    assert os.path.exists(pdf_path), f'Sample synthetic PDF missing at {pdf_path}'

    # 1. OCR Extraction
    ocr_res = process_document_ocr(pdf_path)
    assert ocr_res.get('status') == 'COMPLETED'
    assert ocr_res.get('engine') == 'LandGuard Digital PDF Engine'
    assert ocr_res.get('confidence', 0.0) >= 88.0

    raw_text = ocr_res.get('text', '')
    assert 'Arun Kumar' in raw_text
    assert 'SY-TEST-104/2' in raw_text
    assert '240 square yards' in raw_text
    assert 'Green Valley' in raw_text
    assert 'Demo District' in raw_text
    assert 'DOC-TEST-2026-001' in raw_text
    assert '15 September 2026' in raw_text
    assert 'Rajesh Kumar Sharma' not in raw_text
    assert '402/B' not in raw_text
    assert '2.45 Acres' not in raw_text
    assert '2.45' not in raw_text

    # 2. NLP Information Extraction
    nlp_res = nlp_engine.extract_information(raw_text)
    assert nlp_res.get('status') == 'SUCCESS'
    fields = nlp_res.get('extracted_fields', {})

    assert fields.get('owner_name') == 'Arun Kumar'
    assert fields.get('survey_number') == 'SY-TEST-104/2'
    assert fields.get('land_area_raw') == '240 square yards'
    assert fields.get('land_area_unit') == 'square yards'
    assert fields.get('land_area_numeric') == 240.0
    assert fields.get('land_area_normalized_acres') == 0.0496
    assert abs(fields.get('land_area_acres') - 0.0496) < 1e-4
    assert fields.get('village') == 'Green Valley'
    assert fields.get('district') == 'Demo District'
    assert fields.get('registration_number') == 'DOC-TEST-2026-001'
    assert fields.get('registration_date') == '15 September 2026'

    boundaries = fields.get('boundary_details', {})
    assert boundaries.get('north') == 'Demo Plot SY-TEST-103'
    assert boundaries.get('south') == 'Demo Road'
    assert boundaries.get('east') == 'Demo Plot SY-TEST-105'
    assert boundaries.get('west') == 'Demo Drain'


def test_upload_api_and_isolation():
    # Setup isolated test database for API
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()

    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'sample_data', 'LandGuard_Synthetic_Test_Land_Record.pdf'))
    with open(pdf_path, 'rb') as f:
        file_bytes = f.read()

    # Upload 1: Arun Kumar Synthetic PDF
    up1 = UploadFile(filename='LandGuard_Synthetic_Test_Land_Record.pdf', file=io.BytesIO(file_bytes))
    data1 = asyncio.run(upload_document(file=up1, db=db))

    doc_id_1 = data1.get('document_id')
    assert doc_id_1 is not None
    assert doc_id_1.startswith('DOC-')
    assert data1['extracted_nlp_fields']['owner_name'] == 'Arun Kumar'
    assert data1['extracted_nlp_fields']['survey_number'] == 'SY-TEST-104/2'
    assert data1['extracted_nlp_fields']['land_area_raw'] == '240 square yards'

    # Upload 2: Sample Deed PNG
    sample_png = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'sample_data', 'sample_deed.png'))
    with open(sample_png, 'rb') as f:
        png_bytes = f.read()

    up2 = UploadFile(filename='sample_deed.png', file=io.BytesIO(png_bytes))
    data2 = asyncio.run(upload_document(file=up2, db=db))

    doc_id_2 = data2.get('document_id')
    assert doc_id_2 is not None
    assert doc_id_2.startswith('DOC-')

    # Assert Document IDs are strictly unique per upload
    assert doc_id_1 != doc_id_2

    # Assert Document 2 data does NOT bleed into Document 1 or vice-versa
    get_doc1 = get_document_details(doc_id_1, db=db)
    assert get_doc1['extracted_owner_name'] == 'Arun Kumar'
    assert get_doc1['extracted_survey_number'] == 'SY-TEST-104/2'

    get_doc2 = get_document_details(doc_id_2, db=db)
    assert get_doc2['extracted_owner_name'] in ['Rajesh Kumar Sharma', 'Rajosh Kumar Sharma']
    assert get_doc2['extracted_survey_number'] in ['402/B', '402/8']


def test_unreadable_file_never_returns_mock_text():
    # Pass a corrupted or unreadable text file disguised as PDF
    dummy_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'dummy_empty.pdf'))
    with open(dummy_path, 'wb') as f:
        f.write(b"%PDF-1.4\n1 0 obj\n<<\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF\n")

    try:
        res = process_document_ocr(dummy_path)
        assert res.get('status') in ['UNREADABLE', 'WARNING', 'FAILED']
        assert 'Rajesh Kumar Sharma' not in res.get('text', '')
        assert '402/B' not in res.get('text', '')
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == '__main__':
    test_synthetic_pdf_ocr_and_nlp_extraction()
    test_upload_api_and_isolation()
    test_unreadable_file_never_returns_mock_text()
    print('All PDF OCR & Upload tests passed successfully!')
