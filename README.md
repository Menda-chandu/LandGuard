# LandGuard

LandGuard is a student prototype for OCR, land record validation, ownership-history checks, parcel boundary comparison, and explainable fraud-risk review.

## Main database: PostgreSQL

PostgreSQL is the application database. Docker Compose provides PostgreSQL 16 with a persistent volume and a localhost-only port. SQLite is used for isolated tests and migration backups.

1. Create a Python virtual environment and install `backend/requirements.txt` plus `pytest` and `httpx` for tests. Install Tesseract; scanned PDFs also need Poppler.
2. Copy `.env.example` to `.env` and choose a password. The application reads this file automatically. Keep it private.
3. Start the database from the repository root:

```bash
docker compose up -d postgres
```

4. Import the supplied dataset ZIP (set `LANDGUARD_DATASET_DIR` in `.env` to the same asset directory):

```bash
.venv/bin/python database/import_dataset.py /path/to/LandGuard_Synthetic_Dataset.zip --assets-dir sample_data
```

To migrate an existing SQLite installation, back up its file first, then run:

```bash
.venv/bin/python database/migrate_sqlite_to_postgres.py .venv/landguard.db
```

The migration preserves record IDs, uploads, verification results, and risk assessments. Conflicting destination rows cause a rollback. New upload bytes are stored in PostgreSQL in `document_files`; local copies are also retained unless `KEEP_LOCAL_UPLOADS=0`. Preserve `uploads/` for older uploads that predate database file storage. An explicit `DATABASE_URL` environment variable overrides the PostgreSQL connection settings.

5. Start the API and frontend in separate terminals:

```bash
cd backend
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Frontend: http://127.0.0.1:3000/ · API: http://127.0.0.1:8000/docs · Database status: http://127.0.0.1:8000/api/health

Stop the database with `docker compose stop postgres`. The persistent volume retains its data. Do not use `down -v` unless you intend to delete it.

## Implemented workflow

- PDF/image ingestion, Tesseract OCR, and digital-PDF extraction.
- Rule-based field extraction, including registration details, cardinal boundary descriptions, and labelled English/Telugu Pahani/Adangal fields.
- Owner, survey, normalized acreage, jurisdiction, registration number/date, duplicate registry, and historical ownership checks. Rapid transfers are detected in any 60-day history window.
- Duplicate uploads detected using SHA-256 file bytes and sufficiently long normalized OCR text. Repeat uploads are review signals, not proof of fraud. Different scans with substantially different OCR output may evade exact normalized-text matching.
- Attach a claimed WGS84 GeoJSON Polygon/MultiPolygon in Verification Results. The backend projects both polygons into local metric coordinates and calculates missing land, land outside the reference boundary, and encroachment into neighboring parcels. A 2% symmetric-difference tolerance is used. The map renders the attached claim rather than a fixed demonstration overlay.
- Cardinal boundary descriptions are compared when reference descriptions exist in parcel properties under `boundary_details`. The supplied dataset lacks these descriptions, so those checks display `REFERENCE_UNAVAILABLE`. A missing claim displays `NOT_PROVIDED`; neither status means a match.
- Explainable weighted anomaly score, plus a bounded 10-point advisory Isolation Forest signal when the document is in the most unusual 5% of reference features. The model learns acreage, registry multiplicity, history length, and transfer frequency from at least 20 imported records. The outlier percentile is not fraud probability; feature deviations are descriptive explanations, not causal model attributions.
- Real database search, registry detail/history, saved document results, and dashboard counts.

Application startup applies additive document-evidence migrations. Existing PostgreSQL installations with older area precision should also apply `database/migrations/001_document_area_precision.sql`.

## Demonstration data and limits

The provided dataset contains 122 synthetic registry rows and 220 synthetic ownership-history rows; it is not a government integration. Geographic shapes are illustrative and may not have the same acreage as registry attributes. Geometric areas and registry acreage are reported separately.

`sample_data/pahani_demo.pdf` and `pahani_demo.png` are labelled English Pahani fixtures verified through the actual extraction pipeline. `pahani_demo.boundary.geojson` is an explicitly synthetic matching boundary for that fixture. Telugu label parsing is tested on text. Telugu scan OCR requires installed `tel.traineddata` and `OCR_LANGUAGES=eng+tel`; accuracy on real Telugu scans and unlabelled multi-row tables has not been established.

Registration validation now exposes inconsistencies in the original sample deed fixtures: an owner/survey match does not imply their deed registration number/date match the registry. Samples are not forced to pass.

No measured real-world fraud accuracy, legal-title certification, or time-saving benchmark is claimed. A `VERIFIED` result refers only to the available checks; inspect the evidence coverage for unchecked items.

## Tests

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 DATABASE_URL=sqlite:///:memory: .venv/bin/python -m pytest -q backend/tests
TEST_POSTGRES=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q backend/tests/test_presentation_features.py
cd frontend
npm run lint
npm test
npm run build
```

PostgreSQL tests create randomly named temporary schemas and remove only those schemas. They cover registration mismatches, duplicate evidence, polygon differences/encroachment, description mismatches, boundary API persistence, repeat risk assessment under foreign keys, transfer windows, and learned anomaly scoring. Additional tests exercise actual Pahani PDF and image OCR.

## Stack

React/Vite/Tailwind/Leaflet → FastAPI/SQLAlchemy → PostgreSQL. Tesseract/Pillow/pypdf handle document extraction; Shapely/PyProj handle geometry; scikit-learn supplies Isolation Forest. Field extraction and the primary explainable verification rules remain deterministic.

## Render deployment

`Dockerfile.render` builds React and runs it with FastAPI at the same origin. It includes Tesseract English/Telugu language files and Poppler. `render.yaml` defines a free web service and free PostgreSQL in Singapore; the database connection is wired internally. No local `.env`, uploaded documents, or virtual environment is copied into the image.

The service seeds the 122 synthetic registry rows and 220 histories only when the reference tables are empty. Upload bytes are kept in PostgreSQL, so app restarts do not lose them. The file endpoint is `GET /api/documents/{document_id}/file`. Existing local uploads need to be re-uploaded or migrated separately if they are required on the cloud deployment.

Render free PostgreSQL expires after 30 days and has a 1 GB storage limit. The free service also sleeps when idle. This configuration is for a demonstration; upgrade the database before expiry for longer retention. Back up the database, including `document_files`, if preserving uploads.

To reproduce the deployment, connect the GitHub fork to a Render Blueprint and apply `render.yaml`. The readiness endpoint `/api/health` returns 503 when PostgreSQL is disconnected.
