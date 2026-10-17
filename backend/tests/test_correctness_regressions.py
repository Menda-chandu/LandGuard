import sys
from pathlib import Path
from datetime import date
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from app.database import Base, get_db
from app.models import LandRecord, OwnershipHistory, DocumentRecord
from app.api import documents, registry
from app.nlp.extractor import nlp_engine
from app.verification.engine import verification_engine
from app.gis.spatial_engine import gis_spatial_engine


@pytest.mark.parametrize('extent,expected', [
    ('240 square yards', 240 / 4840), ('43560 square feet', 1),
    ('1 hectare', 2.4710538147), ('40 guntas', 1), ('2.45 acres', 2.45),
])
def test_area_units_are_normalized_without_consuming_following_fields(extent, expected):
    fields = nlp_engine.extract_information(f'Land area: {extent}\nVillage: Green Valley\nMandal: Demo\n')['extracted_fields']
    assert fields['land_area_acres'] == pytest.approx(expected, abs=0.000001)
    assert fields['land_area_raw'] == extent
    assert '\n' not in fields['land_area_unit']
    assert fields['village'] == 'Green Valley'


def test_unknown_area_unit_is_not_assumed_to_be_acres():
    fields = nlp_engine.extract_information('Land area: 240 widgets\n')['extracted_fields']
    assert fields['land_area_acres'] is None


def test_extraction_preserves_ambiguous_names_and_numeric_subdivisions():
    fields = nlp_engine.extract_information('Owner name: Rajosh Kumar\nSurvey number: 101/8\n')['extracted_fields']
    assert fields['owner_name'] == 'Rajosh Kumar'
    assert fields['survey_number'] == '101/8'


def test_owner_matching_requires_the_complete_name():
    assert not verification_engine._compare_names('Rajesh Kumar Sharma', 'Rajesh Kumar Reddy')
    assert verification_engine._compare_names('  ANIL  KUMAR RAO ', 'Anil Kumar Rao')
    assert verification_engine._compare_names('A. Rao', 'A Rao')


def test_labelled_document_type_takes_precedence_over_disclaimer_text():
    fields = nlp_engine.extract_information('Not an official title deed.\nRecord type\nSynthetic sale-record summary\n')['extracted_fields']
    assert fields['document_type'] == 'Sale Deed'


def test_mandal_mismatch_is_detected_without_changing_cached_parcels():
    result = gis_spatial_engine.verify_spatial_location('SYN-101/A', doc_village='Narsingi', doc_mandal='Wrong Mandal', doc_district='Ranga Reddy')
    assert not result['spatial_match']
    assert any(a['title'] == 'Mandal Jurisdiction Mismatch' for a in result['anomalies'])


def test_registry_search_and_detail_never_create_uploaded_documents():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as db:
        db.add(LandRecord(record_id='SYN-REC-001', owner_name='Rajesh Kumar Reddy', survey_number='SYN-101/A', land_area_acres=2.2, village='Narsingi', mandal='Gandipet', district='Ranga Reddy', state='Telangana', document_type='Gift Deed'))
        db.add(OwnershipHistory(history_id='H1', owner_name='Rajesh Kumar Reddy', survey_number='SYN-101/A', transfer_date=date(2020, 1, 1), transfer_type='Gift Deed'))
        db.commit()
        app = FastAPI()
        app.include_router(documents.router, prefix='/api/documents')
        app.include_router(registry.router, prefix='/api/registry')
        app.dependency_overrides[get_db] = lambda: db
        with TestClient(app) as client:
            search = client.get('/api/documents/search', params={'q': 'SYN101A'}).json()
            assert search['count'] == 1
            assert search['results'][0]['type'] == 'land_record'
            result = client.get('/api/registry/SYN-REC-001').json()
            assert result['owner_name'] == 'Rajesh Kumar Reddy'
            assert len(result['history_timeline']) == 1
            assert 'document_id' not in result
            assert db.query(DocumentRecord).count() == 0
            assert client.get('/api/registry/missing').status_code == 404
        # Sharing two name words must not turn an impostor into a verified owner.
        result = verification_engine.verify_extracted_attributes('Rajesh Kumar Sharma', 'SYN-101/A', 2.2, db=db)
        assert result['verification_status'] == 'SUSPICIOUS'
        assert any(a['type'] == 'OWNER_NAME_MISMATCH' for a in result['detected_anomalies'])
        # An enrichment request must not overwrite the independent GIS evidence.
        db.query(LandRecord).filter_by(record_id='SYN-REC-001').update({'mandal': 'Wrong Mandal'})
        db.commit()
        gis_spatial_engine.get_parcel_by_survey('SYN-101/A', db)
        assert gis_spatial_engine.get_parcel_by_survey('SYN-101/A')['properties']['mandal'] == 'Gandipet'
    engine.dispose()
