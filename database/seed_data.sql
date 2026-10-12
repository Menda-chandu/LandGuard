-- ====================================================================
-- LandGuard Initial Seed Data SQL Script
-- Source: sample_data/land_records.csv & sample_data/ownership_history.csv
-- ====================================================================

-- 1. Insert Land Records
INSERT INTO land_records (record_id, owner_name, survey_number, land_area_acres, village, mandal, district, state, registration_number, registration_date, document_type) VALUES
('REC-1001', 'Anil Kumar Rao', '101/A', 2.50, 'Greenvalley', 'Serilingampally', 'Ranga Reddy', 'Telangana', 'REG-2020-00101', '2020-03-15', 'Sale Deed'),
('REC-1002', 'Bhavana Sharma', '102/B', 1.80, 'Greenvalley', 'Serilingampally', 'Ranga Reddy', 'Telangana', 'REG-2021-00204', '2021-06-20', 'Sale Deed'),
('REC-1003', 'Chandra Shekhar Verma', '103/C', 4.20, 'Sunnyside', 'Rajendranagar', 'Ranga Reddy', 'Telangana', 'REG-2019-00305', '2019-11-10', 'Gift Deed'),
('REC-1004', 'Deepak Patel', '104/A', 3.10, 'Sunnyside', 'Rajendranagar', 'Ranga Reddy', 'Telangana', 'REG-2022-00412', '2022-01-05', 'Partition Deed'),
('REC-1005', 'Esha Reddy', '105/D', 0.95, 'Lakeview', 'Shamshabad', 'Ranga Reddy', 'Telangana', 'REG-2023-00520', '2023-08-14', 'Sale Deed'),
('REC-1006', 'Farhan Ahmed', '201/A', 5.00, 'Hilltop', 'Maheshwaram', 'Ranga Reddy', 'Telangana', 'REG-2018-00615', '2018-04-12', 'Sale Deed'),
('REC-1007', 'Gita Devi', '202/B', 2.15, 'Hilltop', 'Maheshwaram', 'Ranga Reddy', 'Telangana', 'REG-2021-00722', '2021-09-30', 'Sale Deed'),
('REC-1008', 'Harish Chandra', '301/A', 1.50, 'Meadowlands', 'Kandukur', 'Ranga Reddy', 'Telangana', 'REG-2020-00830', '2020-12-01', 'Sale Deed'),
('REC-1009', 'Indira Nair', '302/X', 3.80, 'Meadowlands', 'Kandukur', 'Ranga Reddy', 'Telangana', 'REG-2022-00945', '2022-05-18', 'Partition Deed'),
('REC-1010', 'Jayant Joshi', '401/A', 1.80, 'Riverside', 'Ibrahimpatnam', 'Ranga Reddy', 'Telangana', 'REG-2019-01050', '2019-02-28', 'Sale Deed'),
('REC-1011', 'Kiran Mazumdar', '402/B', 2.00, 'Riverside', 'Ibrahimpatnam', 'Ranga Reddy', 'Telangana', 'REG-2023-01160', '2023-04-10', 'Sale Deed'),
('REC-1012', 'Lokesh Gupta', '501/A', 4.00, 'Forest Edge', 'Moinabad', 'Ranga Reddy', 'Telangana', 'REG-2021-01270', '2021-10-15', 'Sale Deed'),
('REC-1013', 'Madhav Singh', '501/A', 4.00, 'Forest Edge', 'Moinabad', 'Ranga Reddy', 'Telangana', 'REG-2023-01380', '2023-11-20', 'Sale Deed'),
('REC-1014', 'Nitin Saxena', '601/A', 2.75, 'Highland', 'Chevella', 'Ranga Reddy', 'Telangana', 'REG-2024-01490', '2024-01-10', 'Sale Deed'),
('REC-1015', 'Omkar Kulkarni', '602/B', 1.25, 'Highland', 'Chevella', 'Ranga Reddy', 'Telangana', 'REG-2024-01501', '2024-02-05', 'Gift Deed'),
('REC-1016', 'Pooja Hegde', '701/A', 3.00, 'Valleyview', 'Shadnagar', 'Ranga Reddy', 'Telangana', 'REG-2020-01612', NULL, 'Sale Deed'),
('REC-1017', NULL, '702/B', 2.20, 'Valleyview', 'Shadnagar', 'Ranga Reddy', 'Telangana', 'REG-2022-01725', '2022-07-22', 'Patta Passbook'),
('REC-1018', 'Qasim Ali', '703/C', 0.00, 'Valleyview', 'Shadnagar', 'Ranga Reddy', 'Telangana', 'REG-2021-01833', '2021-03-19', 'Sale Deed'),
('REC-1019', 'Rameshwar Prasad', '801/A', 6.50, 'Sunrise', 'Farooqnagar', 'Ranga Reddy', 'Telangana', 'REG-2017-01944', '2017-05-11', 'Inheritance Mutation'),
('REC-1020', 'Suresh Babu', '802/B', 1.10, 'Sunrise', 'Farooqnagar', 'Ranga Reddy', 'Telangana', 'REG-2023-02055', '2023-09-09', 'Sale Deed'),
('REC-1021', 'Tarun Chawla', '901/A', 2.90, 'Lakeside', 'Hayathnagar', 'Ranga Reddy', 'Telangana', 'REG-2022-02166', '2022-11-30', 'Sale Deed'),
('REC-1022', 'Uma Devi', '902/B', 4.80, 'Lakeside', 'Hayathnagar', 'Ranga Reddy', 'Telangana', 'REG-2019-02277', '2019-08-17', 'Gift Deed')
ON CONFLICT (record_id) DO NOTHING;


-- 2. Insert Ownership History
INSERT INTO ownership_history (history_id, survey_number, owner_name, transfer_date, transfer_type) VALUES
('HIST-001', '101/A', 'Ramakrishna Rao', '1995-04-10', 'Original Grant'),
('HIST-002', '101/A', 'Anil Kumar Rao', '2020-03-15', 'Sale Deed'),
('HIST-003', '102/B', 'Govind Sharma', '1998-08-12', 'Original Grant'),
('HIST-004', '102/B', 'Bhavana Sharma', '2021-06-20', 'Sale Deed'),
('HIST-005', '103/C', 'Chandra Shekhar Verma', '2019-11-10', 'Gift Deed'),
('HIST-006', '201/A', 'Farhan Ahmed', '2018-04-12', 'Sale Deed'),
('HIST-007', '202/B', 'Gita Devi', '2021-09-30', 'Sale Deed'),
('HIST-008', '301/A', 'Harish Chandra', '2020-12-01', 'Sale Deed'),
('HIST-009', '401/A', 'Mukund Joshi', '2002-01-12', 'Original Grant'),
('HIST-010', '401/A', 'Jayant Joshi', '2019-02-28', 'Inheritance Mutation'),
('HIST-011', '402/B', 'Subhash Mazumdar', '2005-07-14', 'Original Grant'),
('HIST-012', '402/B', 'Kiran Mazumdar', '2023-04-10', 'Sale Deed'),
('HIST-013', '501/A', 'Lokesh Gupta', '2021-10-15', 'Sale Deed'),
('HIST-014', '501/A', 'Madhav Singh', '2023-11-20', 'Duplicate Sale Deed'),
('HIST-015', '601/A', 'Anand Saxena', '2023-12-01', 'Original Sale'),
('HIST-016', '601/A', 'Vijay Saxena', '2023-12-15', 'Rapid Resale'),
('HIST-017', '601/A', 'Nitin Saxena', '2024-01-10', 'Rapid Resale'),
('HIST-018', '602/B', 'Omkar Kulkarni', '2024-02-05', 'Gift Deed (No Prior History)'),
('HIST-019', '801/A', 'Bishwanath Prasad', '1988-06-20', 'Original Grant'),
('HIST-020', '801/A', 'Rameshwar Prasad', '2017-05-11', 'Inheritance Mutation'),
('HIST-021', '901/A', 'Harpreet Chawla', '2010-09-05', 'Sale Deed'),
('HIST-022', '901/A', 'Tarun Chawla', '2022-11-30', 'Sale Deed')
ON CONFLICT (history_id) DO NOTHING;


-- 3. Initial Document Record Sample Entry
INSERT INTO document_records (document_id, filename, file_path, file_type, file_size_bytes, ocr_status, extracted_text, extracted_owner_name, extracted_survey_number, extracted_land_area, extracted_location, ocr_confidence_score) VALUES
('DOC-2026-8901', 'Sale_Deed_Plot_402B.pdf', 'uploads/Sale_Deed_Plot_402B.pdf', 'PDF', 2516582, 'COMPLETED', 'Extracted OCR content for plot 402/B executant Rajesh Kumar Sharma claimed area 2.45 Acres', 'Rajesh Kumar Sharma', '402/B', 2.45, 'Village Gachibowli, Plot 402/B, RR District', 96.40)
ON CONFLICT (document_id) DO NOTHING;


-- 4. Initial Verification Result Entry
INSERT INTO verification_results (verification_id, document_id, matched_record_id, owner_match, survey_number_match, land_area_match, verification_status, detected_anomalies) VALUES
('VER-2026-001', 'DOC-2026-8901', 'REC-1011', FALSE, TRUE, FALSE, 'SUSPICIOUS', 'Owner Mismatch (Document: Rajesh Kumar Sharma vs Registry: Ramesh Chandra Sharma); Area Discrepancy (Claimed: 2.45 Acres vs Registry: 1.80 Acres); Active Encumbrance Lien')
ON CONFLICT (verification_id) DO NOTHING;


-- 5. Initial Risk Assessment Entry
INSERT INTO risk_assessments (assessment_id, verification_id, risk_score, risk_level, ownership_continuity_score, area_discrepancy_score, encumbrance_score, recommendations) VALUES
('RSK-2026-001', 'VER-2026-001', 78, 'High Risk', 85, 75, 90, 'Flag for manual revenue office hearing; request mutation certificate and verify active bank mortgage with State Bank of India.')
ON CONFLICT (assessment_id) DO NOTHING;
