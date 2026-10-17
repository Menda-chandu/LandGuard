-- Apply once to existing PostgreSQL installations after upgrading LandGuard.
-- Existing uploaded files must be re-extracted to correct previously stored units.
ALTER TABLE document_records
    ALTER COLUMN extracted_land_area TYPE NUMERIC(14, 6);
