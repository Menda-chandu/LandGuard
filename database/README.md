# LandGuard Database Documentation

PostgreSQL database module for the **AI-Powered Land Record Validation and Fraud Detection System**.

---

## Entity Relationship & Schema Design

The system utilizes 5 core tables designed with explicit primary keys, foreign keys, and targeted performance indexes:

```text
+---------------------+           +------------------------+
|    land_records     |           |   ownership_history    |
+---------------------+           +------------------------+
| PK record_id        |           | PK history_id          |
|    owner_name       |           |    survey_number       |
|    survey_number    |           |    owner_name          |
|    land_area_acres  |           |    transfer_date       |
|    village          |           |    transfer_type       |
|    mandal/district  |           +------------------------+
|    document_type    |
+---------------------+
           ^
           | (matched_record_id)
+---------------------+           +--------------------------+           +-----------------------+
|  document_records   |           |   verification_results   |           |   risk_assessments    |
+---------------------+           +--------------------------+           +-----------------------+
| PK document_id      | <-------- | PK verification_id       | <-------- | PK assessment_id      |
|    filename         | (FK)      | FK document_id           | (FK)      | FK verification_id    |
|    ocr_status       |           | FK matched_record_id     |           |    risk_score (0-100) |
|    extracted_text   |           |    owner_match (bool)    |           |    risk_level (Cat)   |
|    ocr_confidence   |           |    verification_status   |           |    recommendations    |
+---------------------+           +--------------------------+           +-----------------------+
```

### Table Summary & Primary Keys

1. **`land_records`**
   - **Primary Key:** `record_id` (VARCHAR)
   - **Indexes:** `idx_land_records_survey`, `idx_land_records_owner`, `idx_land_records_district`
   - **Purpose:** Baseline government land revenue registry records.

2. **`ownership_history`**
   - **Primary Key:** `history_id` (VARCHAR)
   - **Indexes:** `idx_ownership_history_survey`, `idx_ownership_history_transfer_date`
   - **Purpose:** Tracks historical title chains and past deed transactions.

3. **`document_records`**
   - **Primary Key:** `document_id` (VARCHAR)
   - **Indexes:** `idx_document_records_status`
   - **Purpose:** Scanned document uploads, file metadata, and raw OCR extracted fields.

4. **`verification_results`**
   - **Primary Key:** `verification_id` (VARCHAR)
   - **Foreign Keys:** `document_id` -> `document_records(document_id)`, `matched_record_id` -> `land_records(record_id)`
   - **Indexes:** `idx_verification_doc_id`, `idx_verification_status`
   - **Purpose:** Attribute-by-attribute comparison matrix and flagged discrepancies.

5. **`risk_assessments`**
   - **Primary Key:** `assessment_id` (VARCHAR)
   - **Foreign Key:** `verification_id` -> `verification_results(verification_id)`
   - **Indexes:** `idx_risk_assessments_ver_id`, `idx_risk_assessments_level`
   - **Purpose:** Computed fraud risk score (0-100), risk tier (`Low Risk`, `Medium Risk`, `High Risk`), and revenue officer recommendation flags.

---

## How to Setup & Initialize Database

### Option A: Automated Python Setup (Recommended)
Make sure `psycopg2-binary` is installed:
```bash
pip install psycopg2-binary
```
Run the automated script (pass your PostgreSQL password if prompted):
```bash
python database/init_db.py --password YOUR_POSTGRES_PASSWORD
```

---

### Option B: Manual Setup using `psql` CLI

#### 1. Create the Database
```bash
psql -U postgres -c "CREATE DATABASE landguard_db;"
```

#### 2. Run Schema Migrations
```bash
psql -U postgres -d landguard_db -f database/schema.sql
```

#### 3. Load Sample Seed Data
```bash
psql -U postgres -d landguard_db -f database/seed_data.sql
```

#### 4. Verify Tables & Records
```bash
psql -U postgres -d landguard_db -c "SELECT COUNT(*) FROM land_records;"
psql -U postgres -d landguard_db -c "SELECT COUNT(*) FROM ownership_history;"
```
