# LandGuard - AI-Powered Land Record Validation and Fraud Detection System

LandGuard is a full-stack student project for automated land record validation, OCR title deed processing, rule-based NLP extraction, database verification, explainable risk scoring, and GIS spatial mapping.

> [!NOTE]
> **Synthetic Demonstration Dataset Notice:** All 100 land records, ownership histories, survey numbers, parcel geometries, and verification results in this project are **100% synthetic demonstration data**. They are created strictly for educational and algorithmic testing and **do not constitute official government verification or legal certification**.

---

## Tech Stack
- **Frontend:** React.js, Vite, Tailwind CSS, Leaflet.js
- **Backend:** Python FastAPI, Uvicorn, SQLAlchemy
- **Database:** PostgreSQL (`landguard_db`)
- **OCR:** Tesseract OCR (`pytesseract`, Pillow, pdf2image)
- **NLP:** Rule-Based Regex Extraction Engine
- **GIS:** GeoJSON spatial parcel mapping & location verification

---

## Project Structure
```text
Landguard/
├── frontend/         # React.js SPA (Dashboard, Upload, OCR, Results, Risk, History, GIS)
├── backend/          # FastAPI server, OCR pipeline, NLP parser, Verification & Risk engines
│   └── tests/        # E2E & unit test suites (NLP, Verification, Risk, GIS)
├── database/         # PostgreSQL schema.sql, seed_data.sql, and init_db.py
├── uploads/          # Local storage for uploaded document files
└── sample_data/      # Fictional land records CSV, ownership history, & parcels.geojson
```

---

## How to Run Frontend and Backend Together

### Step 1: Start PostgreSQL Database
Ensure PostgreSQL service is running and initialize `landguard_db`:
```powershell
python database/init_db.py --password YOUR_POSTGRES_PASSWORD
```

### Step 2: Start FastAPI Backend Server
Open a terminal window and execute:
```powershell
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- Backend API running at: `http://127.0.0.1:8000`
- Swagger Interactive Documentation: `http://127.0.0.1:8000/docs`

### Step 3: Start React Frontend Server
Open a second terminal window and execute:
```powershell
cd frontend
npm install
npm run dev
```
- Frontend application running at: `http://localhost:3000`

---

## Running End-to-End Automated Tests
```powershell
# Run Full E2E Pipeline Test (OCR -> NLP -> Verification -> Risk -> GIS):
python backend/tests/test_e2e.py

# Run Individual Module Tests:
python backend/tests/test_nlp.py
python backend/tests/test_verification.py
python backend/tests/test_risk_scoring.py
python backend/tests/test_gis.py
```
