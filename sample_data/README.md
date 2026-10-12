# LandGuard Sample Dataset

This directory contains fictional sample datasets used for testing and validating the **AI-Powered Land Record Validation and Fraud Detection System**.

> [!NOTE]
> All data in this directory is 100% fictional. No real personal details or real government records are used.

---

## File Contents

### 1. `land_records.csv`
Contains baseline official land registry records used by the backend to verify uploaded document details.

#### Field Descriptions:
- `record_id`: Unique primary key for each government revenue land record (e.g., `REC-1001`).
- `owner_name`: Registered legal title owner of the land parcel.
- `survey_number`: Unique Cadastral survey parcel number / sub-division (e.g., `101/A`).
- `land_area_acres`: Officially registered land area measurement in Acres (e.g., `2.50`).
- `village`: Local village name where the plot is located.
- `mandal`: Sub-district / Mandal jurisdiction.
- `district`: District administration division.
- `state`: State jurisdiction.
- `registration_number`: Official government registration document number (e.g., `REG-2020-00101`).
- `registration_date`: Date of legal document registration (`YYYY-MM-DD`).
- `document_type`: Type of legal instrument (`Sale Deed`, `Gift Deed`, `Partition Deed`, `Patta Passbook`, `Inheritance Mutation`).

---

### 2. `ownership_history.csv`
Tracks historical title chains, previous owners, and deed transfers over time for each survey parcel.

#### Field Descriptions:
- `history_id`: Unique identifier for each historical transfer entry (e.g., `HIST-001`).
- `survey_number`: Survey parcel sub-division matching `land_records.csv`.
- `owner_name`: Name of owner during that specific historical period.
- `transfer_date`: Date when ownership was transferred (`YYYY-MM-DD`).
- `transfer_type`: Nature of transfer (`Original Grant`, `Sale Deed`, `Gift Deed`, `Inheritance Mutation`, `Duplicate Sale Deed`, `Rapid Resale`).

---

## Test Cases & Anomaly Map

The dataset includes specific test cases designed to evaluate OCR extraction, database verification, and fraud detection algorithms:

| Test Case Category | Target Record IDs | Target Survey No. | Intended Verification & Fraud Detection Scenario |
| :--- | :--- | :--- | :--- |
| **Clean Verified Matches** | `REC-1001` to `REC-1005`, `REC-1019` to `REC-1022` | `101/A`, `102/B`, `103/C`, `104/A`, `105/D` | Baseline clean records where uploaded deed details perfectly match database registry. |
| **Owner Name Mismatch** | `REC-1006`, `REC-1007` | `201/A`, `202/B` | Tests OCR/NLP identity extraction where document owner name does not match registered title owner. |
| **Survey Number Mismatch** | `REC-1008`, `REC-1009` | `301/A`, `302/X` | Tests survey number validation where document claims non-existent or wrong sub-divisions (`301/B`, `302/Z`). |
| **Land Area Inflation Mismatch** | `REC-1010`, `REC-1011` | `401/A`, `402/B` | Tests land area validation where document claims inflated land area (e.g., 2.90 Acres claimed vs 1.80 Acres in record). |
| **Duplicate Registrations** | `REC-1012`, `REC-1013` | `501/A` | Tests double-selling detection where the same survey plot is registered twice under different sellers. |
| **Rapid Transfer Anomaly** | `REC-1014` | `601/A` | Tests anomaly detection for suspicious rapid ownership flipping (3 transfers within 30 days). |
| **Missing History Chain** | `REC-1015` | `602/B` | Tests title chain continuity checks where a gift deed appears without prior grant/ownership record. |
| **Incomplete Data Handling** | `REC-1016` to `REC-1018` | `701/A`, `702/B`, `703/C` | Tests system resilience against missing registration dates, missing owner names, or 0.00 land area fields. |
