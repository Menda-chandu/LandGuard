import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models import LandRecord, OwnershipHistory, DocumentRecord, VerificationResult
from app.nlp.extractor import nlp_engine
from app.gis.spatial_engine import gis_spatial_engine


class LandVerificationEngine:
    """
    Rule-Based Land Record Verification & Anomaly Detection Engine.
    Cross-matches extracted document NLP attributes against baseline PostgreSQL
    revenue registry land_records, historical ownership_history title chains,
    and GeoJSON CAD spatial polygon boundaries.
    """

    def __init__(self):
        pass

    def verify_document(self, document_id: str, db: Session) -> Dict[str, Any]:
        """
        Main entrypoint to verify a document by document_id.
        Fetches document record, runs NLP extraction if needed, matches against
        land_records, ownership_history, and GIS spatial engine, computes anomalies,
        and persists result.
        """
        doc_record = None
        try:
            doc_record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass

        if not doc_record:
            import os
            from app.api.documents import UPLOADS_DIR
            from app.ocr.processor import process_document_ocr
            matching_files = [f for f in os.listdir(UPLOADS_DIR) if f.startswith(document_id)] if os.path.exists(UPLOADS_DIR) else []
            if matching_files:
                file_path = os.path.join(UPLOADS_DIR, matching_files[0])
                ocr_res = process_document_ocr(file_path)
                extracted_text = ocr_res.get("text", "")
                nlp_res = nlp_engine.extract_information(extracted_text)
                extracted_fields = nlp_res.get("extracted_fields", {})
                owner_name = extracted_fields.get("owner_name")
                survey_number = extracted_fields.get("survey_number")
                land_area = float(extracted_fields.get("land_area_acres") or 0.0)
                village = extracted_fields.get("village")
                mandal = extracted_fields.get("mandal")
                district = extracted_fields.get("district")
                return self.verify_extracted_attributes(
                    owner_name=owner_name,
                    survey_number=survey_number,
                    land_area=land_area,
                    doc_village=village,
                    doc_mandal=mandal,
                    doc_district=district,
                    document_id=document_id,
                    db=db
                )
            return self._build_not_found_response(document_id)

        # 1. Gather Extracted Attributes
        extracted_text = doc_record.extracted_text or ""
        nlp_res = nlp_engine.extract_information(extracted_text)
        extracted_fields = nlp_res.get("extracted_fields", {})

        owner_name = doc_record.extracted_owner_name or extracted_fields.get("owner_name")
        survey_number = doc_record.extracted_survey_number or extracted_fields.get("survey_number")
        land_area = float(doc_record.extracted_land_area or extracted_fields.get("land_area_acres") or 0.0)
        village = extracted_fields.get("village")
        mandal = extracted_fields.get("mandal")
        district = extracted_fields.get("district")

        # 2. Run Verification Logic
        verification_payload = self.verify_extracted_attributes(
            owner_name=owner_name,
            survey_number=survey_number,
            land_area=land_area,
            doc_village=village,
            doc_mandal=mandal,
            doc_district=district,
            document_id=document_id,
            db=db
        )

        # 3. Store Result in PostgreSQL verification_results Table
        ver_id = f"VER-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        anomalies_str = "; ".join([f"{a['title']}: {a['description']}" for a in verification_payload["detected_anomalies"]])

        ver_result_db = VerificationResult(
            verification_id=ver_id,
            document_id=document_id,
            matched_record_id=verification_payload["matched_record_id"],
            owner_match=verification_payload["field_matches"]["owner_match"],
            survey_number_match=verification_payload["field_matches"]["survey_number_match"],
            land_area_match=verification_payload["field_matches"]["land_area_match"],
            verification_status=verification_payload["verification_status"],
            detected_anomalies=anomalies_str
        )

        try:
            db.query(VerificationResult).filter(VerificationResult.document_id == document_id).delete()
            db.add(ver_result_db)
            db.commit()
        except Exception as err:
            db.rollback()
            print(f"Notice: Verification result DB persistence note: {err}")

        verification_payload["verification_id"] = ver_id
        return verification_payload

    def verify_extracted_attributes(
        self,
        owner_name: Optional[str],
        survey_number: Optional[str],
        land_area: float,
        doc_village: Optional[str] = None,
        doc_mandal: Optional[str] = None,
        doc_district: Optional[str] = None,
        document_id: str = "DOC-DEFAULT",
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Pure rule-based verification matrix matching document attributes against DB records & GIS polygons.
        """
        anomalies: List[Dict[str, Any]] = []
        field_matches = {
            "owner_match": False,
            "survey_number_match": False,
            "land_area_match": False,
            "spatial_match": False
        }

        # Check 1: Incomplete Information Check
        if not survey_number:
            anomalies.append({
                "type": "INCOMPLETE_DOCUMENT_DATA",
                "severity": "High",
                "title": "Missing Survey Number",
                "expected": "Valid Cadastral Survey Number (e.g. 101/A, 402/B)",
                "found": "No survey number extracted from document",
                "description": "The uploaded document lacks a recognizable survey parcel number required for database verification."
            })
            return {
                "document_id": document_id,
                "verification_status": "UNVERIFIED",
                "matched_record_id": None,
                "matched_land_record": None,
                "field_matches": field_matches,
                "detected_anomalies": anomalies,
                "anomalies_count": len(anomalies)
            }

        if not owner_name:
            anomalies.append({
                "type": "INCOMPLETE_DOCUMENT_DATA",
                "severity": "Medium",
                "title": "Missing Owner / Executant Name",
                "expected": "Valid title holder / executant name",
                "found": "Empty or unreadable owner name",
                "description": "The executant or owner name could not be identified from the document text."
            })

        if land_area <= 0.0:
            anomalies.append({
                "type": "INCOMPLETE_DOCUMENT_DATA",
                "severity": "Medium",
                "title": "Zero or Invalid Land Area",
                "expected": "Positive land area extent (greater than 0.00 Acres)",
                "found": f"{land_area} Acres",
                "description": "Document specifies zero or invalid land area extent."
            })

        # Check 2: GIS Spatial Verification Check
        spatial_res = gis_spatial_engine.verify_spatial_location(
            survey_number=survey_number,
            doc_village=doc_village,
            doc_mandal=doc_mandal,
            doc_district=doc_district,
            db=db
        )

        if spatial_res.get("spatial_match"):
            field_matches["spatial_match"] = True
        else:
            anomalies.extend(spatial_res.get("anomalies", []))

        # Check 3: Match against land_records table
        matched_record = None
        if db:
            matched_record = db.query(LandRecord).filter(LandRecord.survey_number == survey_number).first()
            if not matched_record:
                base_survey = survey_number.split('/')[0] if '/' in survey_number else survey_number
                matched_record = db.query(LandRecord).filter(LandRecord.survey_number.like(f"{base_survey}%")).first()

        if not matched_record:
            anomalies.append({
                "type": "SURVEY_NOT_FOUND",
                "severity": "High",
                "title": "Unregistered Survey Parcel Number",
                "expected": f"Survey parcel '{survey_number}' registered in government revenue database",
                "found": f"No registry entry found for Survey '{survey_number}'",
                "description": f"Survey number '{survey_number}' does not exist in the official government land records database."
            })
            return {
                "document_id": document_id,
                "verification_status": "SUSPICIOUS",
                "matched_record_id": None,
                "matched_land_record": None,
                "field_matches": field_matches,
                "detected_anomalies": anomalies,
                "anomalies_count": len(anomalies)
            }

        # Matched record details
        matched_record_id = matched_record.record_id
        matched_land_dict = {
            "record_id": matched_record.record_id,
            "owner_name": matched_record.owner_name,
            "survey_number": matched_record.survey_number,
            "land_area_acres": float(matched_record.land_area_acres),
            "village": matched_record.village,
            "mandal": matched_record.mandal,
            "district": matched_record.district,
            "registration_number": matched_record.registration_number,
            "document_type": matched_record.document_type
        }

        # Check 4: Survey Number Match
        if matched_record.survey_number == survey_number:
            field_matches["survey_number_match"] = True
        else:
            anomalies.append({
                "type": "SURVEY_NUMBER_MISMATCH",
                "severity": "High",
                "title": "Survey Sub-division Mismatch",
                "expected": f"Exact Survey Parcel '{matched_record.survey_number}'",
                "found": f"Document Claims Survey '{survey_number}'",
                "description": f"Document claims Survey '{survey_number}', but government record is registered under Survey '{matched_record.survey_number}'."
            })

        # Check 5: Owner Name Match
        if owner_name and matched_record.owner_name:
            if self._compare_names(owner_name, matched_record.owner_name):
                field_matches["owner_match"] = True
            else:
                anomalies.append({
                    "type": "OWNER_NAME_MISMATCH",
                    "severity": "High",
                    "title": "Ownership Name Mismatch Anomaly",
                    "expected": f"Registered Title Owner: '{matched_record.owner_name}'",
                    "found": f"Document Executant Name: '{owner_name}'",
                    "description": f"Document owner name '{owner_name}' does not match official registered owner '{matched_record.owner_name}'."
                })

        # Check 6: Land Area Match (Tolerance +/- 0.05 Acres)
        registered_area = float(matched_record.land_area_acres)
        if land_area > 0.0 and registered_area > 0.0:
            area_diff = round(abs(land_area - registered_area), 2)
            if area_diff <= 0.05:
                field_matches["land_area_match"] = True
            else:
                severity = "High" if area_diff > 0.25 else "Medium"
                anomalies.append({
                    "type": "LAND_AREA_MISMATCH",
                    "severity": severity,
                    "title": "Land Area Discrepancy",
                    "expected": f"Registered Parcel Area: {registered_area} Acres",
                    "found": f"Claimed Document Extent: {land_area} Acres",
                    "description": f"Document claims {land_area} Acres, which differs from official registered area of {registered_area} Acres by {area_diff} Acres."
                })

        # Check 7: Duplicate Registration Check
        if db:
            duplicate_records = db.query(LandRecord).filter(
                LandRecord.survey_number == survey_number,
                LandRecord.record_id != matched_record_id
            ).all()

            if duplicate_records:
                dup_owners = [r.owner_name for r in duplicate_records if r.owner_name]
                anomalies.append({
                    "type": "DUPLICATE_REGISTRATION_FLAGGED",
                    "severity": "Critical",
                    "title": "Duplicate Registration / Double Selling Alert",
                    "expected": f"Single clear title registration for Survey {survey_number}",
                    "found": f"Multiple active registrations under sellers: {', '.join(dup_owners)}",
                    "description": f"Survey parcel {survey_number} is registered under multiple records ({matched_record_id} and {duplicate_records[0].record_id}), indicating potential double registration fraud."
                })

        # Check 8: Ownership History & Rapid Transfer Checks
        if db:
            history_records = db.query(OwnershipHistory).filter(
                OwnershipHistory.survey_number == survey_number
            ).order_by(OwnershipHistory.transfer_date.desc()).all()

            if history_records:
                dates = [h.transfer_date for h in history_records if h.transfer_date]
                if len(dates) >= 3:
                    dates_sorted = sorted(dates, reverse=True)
                    days_span = (dates_sorted[0] - dates_sorted[-1]).days
                    if days_span <= 60:
                        anomalies.append({
                            "type": "RAPID_OWNERSHIP_TRANSFER",
                            "severity": "High",
                            "title": "Suspicious Rapid Ownership Transfer Anomaly",
                            "expected": "Normal title transfer intervals over years",
                            "found": f"{len(dates)} ownership transfers within {days_span} days",
                            "description": f"Parcel {survey_number} underwent {len(dates)} rapid transfers between {dates_sorted[-1]} and {dates_sorted[0]}, triggering suspicious flipping risk."
                        })

                if owner_name:
                    hist_owners = [h.owner_name.lower() for h in history_records if h.owner_name]
                    if not any(self._compare_names(owner_name, ho) for ho in hist_owners):
                        anomalies.append({
                            "type": "UNFOUND_SELLER_IN_HISTORY",
                            "severity": "Medium",
                            "title": "Title Chain Continuity Break",
                            "expected": f"Executant '{owner_name}' present in historical ownership chain",
                            "found": f"Executant missing from title chain records: {', '.join([h.owner_name for h in history_records[:3]])}",
                            "description": f"Owner name '{owner_name}' has no registered historical grant or mutation transfer record for Survey {survey_number}."
                        })
            elif matched_record and owner_name:
                anomalies.append({
                    "type": "MISSING_HISTORICAL_TITLE_CHAIN",
                    "severity": "Medium",
                    "title": "Missing Prior Ownership History",
                    "expected": "Registered historical transfer chain",
                    "found": "No prior transfer records in ownership history database",
                    "description": f"Survey parcel {survey_number} lacks prior transfer history records in database."
                })

        # Determine Final Verification Status
        high_critical_anomalies = [a for a in anomalies if a["severity"] in ["High", "Critical"]]

        if not anomalies:
            status_str = "VERIFIED"
        elif high_critical_anomalies:
            status_str = "SUSPICIOUS"
        else:
            status_str = "REVIEW_NEEDED"

        return {
            "document_id": document_id,
            "verification_status": status_str,
            "matched_record_id": matched_record_id,
            "matched_land_record": matched_land_dict,
            "field_matches": field_matches,
            "detected_anomalies": anomalies,
            "anomalies_count": len(anomalies)
        }

    def _compare_names(self, name1: str, name2: str) -> bool:
        if not name1 or not name2:
            return False
        n1 = re.sub(r"[^\w\s]", "", name1.lower()).strip()
        n2 = re.sub(r"[^\w\s]", "", name2.lower()).strip()

        if n1 == n2:
            return True

        tokens1 = set(n1.split())
        tokens2 = set(n2.split())

        common = tokens1.intersection(tokens2)
        if len(common) >= 2:
            return True

        return False

    def _build_not_found_response(self, document_id: str) -> Dict[str, Any]:
        return {
            "document_id": document_id,
            "verification_status": "UNVERIFIED",
            "matched_record_id": None,
            "matched_land_record": None,
            "field_matches": {
                "owner_match": False,
                "survey_number_match": False,
                "land_area_match": False,
                "spatial_match": False
            },
            "detected_anomalies": [{
                "type": "DOCUMENT_NOT_FOUND",
                "severity": "High",
                "title": "Document Record Not Found",
                "expected": f"Document '{document_id}' present in system database",
                "found": "Document ID not found",
                "description": f"No document entry found for ID '{document_id}'."
            }],
            "anomalies_count": 1
        }


# Singleton export
verification_engine = LandVerificationEngine()
