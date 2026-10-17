-- ====================================================================
-- LandGuard Database Schema
-- System: AI-Powered Land Record Validation and Fraud Detection System
-- Target DB: PostgreSQL (landguard_db)
-- ====================================================================

-- 1. Land Records Table (Baseline Government Revenue Registry)
CREATE TABLE IF NOT EXISTS land_records (
    record_id VARCHAR(50) PRIMARY KEY,
    owner_name VARCHAR(150),
    survey_number VARCHAR(50) NOT NULL,
    land_area_acres NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    village VARCHAR(100) NOT NULL,
    mandal VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    registration_number VARCHAR(100),
    registration_date DATE,
    document_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_land_records_survey ON land_records(survey_number);
CREATE INDEX IF NOT EXISTS idx_land_records_owner ON land_records(owner_name);
CREATE INDEX IF NOT EXISTS idx_land_records_district ON land_records(district);


-- 2. Ownership History Table (Title Chains & Historical Transfers)
CREATE TABLE IF NOT EXISTS ownership_history (
    history_id VARCHAR(50) PRIMARY KEY,
    survey_number VARCHAR(50) NOT NULL,
    owner_name VARCHAR(150) NOT NULL,
    transfer_date DATE,
    transfer_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ownership_history_survey ON ownership_history(survey_number);
CREATE INDEX IF NOT EXISTS idx_ownership_history_transfer_date ON ownership_history(transfer_date);


-- 3. Document Records Table (Uploaded Scanned Title Deeds / PDFs)
CREATE TABLE IF NOT EXISTS document_records (
    document_id VARCHAR(50) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ocr_status VARCHAR(50) DEFAULT 'PENDING',
    extracted_text TEXT,
    extracted_owner_name VARCHAR(150),
    extracted_survey_number VARCHAR(50),
    extracted_land_area NUMERIC(14, 6),
    extracted_location VARCHAR(255),
    ocr_confidence_score NUMERIC(5, 2),
    content_sha256 VARCHAR(64),
    text_sha256 VARCHAR(64),
    claimed_geometry TEXT
);

CREATE INDEX IF NOT EXISTS idx_document_records_status ON document_records(ocr_status);
CREATE INDEX IF NOT EXISTS ix_document_records_content_sha256 ON document_records(content_sha256);
CREATE INDEX IF NOT EXISTS ix_document_records_text_sha256 ON document_records(text_sha256);

-- Original uploads survive application redeploys without a local disk.
CREATE TABLE IF NOT EXISTS document_files (
    document_id VARCHAR(50) PRIMARY KEY REFERENCES document_records(document_id) ON DELETE CASCADE,
    content BYTEA NOT NULL,
    media_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- 4. Verification Results Table (Attribute Matching Matrix)
CREATE TABLE IF NOT EXISTS verification_results (
    verification_id VARCHAR(50) PRIMARY KEY,
    document_id VARCHAR(50) NOT NULL REFERENCES document_records(document_id) ON DELETE CASCADE,
    matched_record_id VARCHAR(50) REFERENCES land_records(record_id) ON DELETE SET NULL,
    owner_match BOOLEAN DEFAULT FALSE,
    survey_number_match BOOLEAN DEFAULT FALSE,
    land_area_match BOOLEAN DEFAULT FALSE,
    verification_status VARCHAR(50) NOT NULL DEFAULT 'UNVERIFIED',
    detected_anomalies TEXT,
    verification_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_verification_doc_id ON verification_results(document_id);
CREATE INDEX IF NOT EXISTS idx_verification_status ON verification_results(verification_status);


-- 5. Risk Assessments Table (Fraud Scoring Engine Results)
CREATE TABLE IF NOT EXISTS risk_assessments (
    assessment_id VARCHAR(50) PRIMARY KEY,
    verification_id VARCHAR(50) NOT NULL REFERENCES verification_results(verification_id) ON DELETE CASCADE,
    risk_score INT NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'Low Risk', 'Medium Risk', 'High Risk', 'Critical Risk')),
    ownership_continuity_score INT DEFAULT 0,
    area_discrepancy_score INT DEFAULT 0,
    encumbrance_score INT DEFAULT 0,
    recommendations TEXT,
    assessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_assessments_ver_id ON risk_assessments(verification_id);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_level ON risk_assessments(risk_level);
