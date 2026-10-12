# LandGuard Backend API, OCR, NLP, Verification, Risk & GIS Engine

FastAPI backend service for the **AI-Powered Land Record Validation and Fraud Detection System**.

---

## Architecture & API Modules
```text
backend/
├── app/
│   ├── api/
│   │   ├── health.py            # GET /api/health
│   │   ├── documents.py         # POST /api/documents/upload, GET /api/documents/{id}/nlp
│   │   ├── verification.py      # POST /api/verification/verify/{id}
│   │   ├── risk.py              # POST /api/risk/assess/{id}
│   │   └── gis.py               # GET /api/gis/parcels, POST /api/gis/verify-spatial
│   ├── ocr/
│   │   └── processor.py         # Tesseract OCR engine, image preprocessing & fallback
│   ├── nlp/
│   │   └── extractor.py         # Rule-based NLP entity extraction engine
│   ├── verification/
│   │   └── engine.py            # Land record verification & anomaly detection engine
│   ├── risk_scoring/
│   │   └── engine.py            # Explainable risk scoring engine (0-100 score)
│   ├── gis/
│   │   └── spatial_engine.py    # CAD GeoJSON parcel boundary & spatial verification engine
│   ├── config.py                # Environment & Database settings
│   ├── database.py              # SQLAlchemy engine & session provider
│   ├── models.py                # Database ORM models
│   └── main.py                  # FastAPI application entrypoint
└── tests/
    ├── test_nlp.py              # Automated NLP extraction test suite
    ├── test_verification.py     # Automated Land Record Verification test suite
    ├── test_risk_scoring.py     # Automated Risk Scoring test suite
    └── test_gis.py              # Automated GIS Spatial Mapping test suite
```

---

## GIS Spatial Mapping & GeoJSON Engine

The GIS module connects Cadastral survey numbers (`101/A`, `402/B`, `501/A`, etc.) to spatial polygon geometries stored in `sample_data/parcels.geojson` for OpenStreetMap rendering and spatial verification.

### GeoJSON Parcel Feature Structure Example:
```json
{
  "type": "Feature",
  "id": "PARCEL-101A",
  "properties": {
    "survey_number": "101/A",
    "owner_name": "Anil Kumar Rao",
    "land_area_acres": 2.5,
    "village": "Greenvalley",
    "mandal": "Serilingampally",
    "district": "Ranga Reddy",
    "state": "Telangana",
    "risk_level": "LOW",
    "conflict_status": "Clean"
  },
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [78.3480, 17.4410],
        [78.3495, 17.4415],
        [78.3500, 17.4395],
        [78.3485, 17.4390],
        [78.3480, 17.4410]
      ]
    ]
  }
}
```

---

## GIS API Endpoints

### 1. Retrieve All Parcels (GeoJSON FeatureCollection)
`GET /api/gis/parcels`
Returns all land parcel polygons enriched with live database properties (owner, area, location, risk level) for Leaflet.js rendering.

### 2. Retrieve Specific Parcel by Survey Number
`GET /api/gis/parcels/{survey_number}`
Returns GeoJSON polygon feature for a given survey sub-division.

### 3. Verify Spatial Location Consistency
`POST /api/gis/verify-spatial`
Compares document location claims (village, mandal, district) against official CAD GIS parcel boundaries.

---

## Running Automated Test Suites
```bash
# Run NLP Entity Extraction Tests:
python backend/tests/test_nlp.py

# Run Land Record Verification Tests:
python backend/tests/test_verification.py

# Run Explainable Risk Scoring Tests:
python backend/tests/test_risk_scoring.py

# Run GIS Spatial Mapping Tests:
python backend/tests/test_gis.py
```
