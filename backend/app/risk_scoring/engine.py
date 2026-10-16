import uuid
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from app.models import RiskAssessment, VerificationResult, DocumentRecord
from app.verification.engine import verification_engine


class ExplainableRiskScoringEngine:
    """
    Transparent, Two-Tier Explainable Risk Scoring Engine for LandGuard.
    Distinguishes potential record inconsistencies (fraud risk) from data-quality
    warnings (legibility/missing data). Never penalizes absent synthetic reference records.
    """

    def __init__(self):
        # Explicit Rule Weights
        # 1. Record Inconsistencies (Potential Title Inconsistencies)
        self.INCONSISTENCY_WEIGHTS = {
            "DUPLICATE_REGISTRATION_FLAGGED": 30,
            "OWNER_NAME_MISMATCH": 25,
            "SURVEY_NUMBER_MISMATCH": 20,
            "LAND_AREA_MISMATCH": 20,
            "SPATIAL_LOCATION_MISMATCH": 20,
            "RAPID_OWNERSHIP_TRANSFER": 15,
            "UNFOUND_SELLER_IN_HISTORY": 15,
            "UNFOUNDED_SELLER_IN_HISTORY": 15,
            "MISSING_HISTORICAL_TITLE_CHAIN": 15
        }

        # 2. Data Quality & Legibility Warnings (Informational, NOT fraud)
        self.DATA_QUALITY_WEIGHTS = {
            "INCOMPLETE_DOCUMENT_DATA": 10,
            "LOW_OCR_CONFIDENCE": 5,
        }

        # 3. Informational / Absent Reference (Explicitly 0 points)
        self.ZERO_POINT_TYPES = {
            "REFERENCE_RECORD_NOT_AVAILABLE",
            "SURVEY_NOT_FOUND",
            "GIS_PARCEL_NOT_FOUND",
            "DOCUMENT_NOT_FOUND"
        }

    def compute_risk_assessment(self, document_id: str, db: Session) -> Dict[str, Any]:
        """
        Computes risk score and level for a given document_id, persists the result
        in risk_assessments table, and returns an explainable breakdown.
        """
        # 1. Run or fetch verification results for document
        verification_payload = verification_engine.verify_document(document_id, db)
        verification_id = verification_payload.get("verification_id", f"VER-{document_id}")
        detected_anomalies = verification_payload.get("detected_anomalies", [])
        ver_status = verification_payload.get("verification_status", "UNVERIFIED")

        # 2. Compute Two-Tier Risk Score
        inconsistency_breakdown = []
        quality_breakdown = []
        info_breakdown = []

        inconsistency_score = 0
        quality_score = 0

        for issue in detected_anomalies:
            issue_type = issue.get("type", "UNKNOWN")

            if issue_type in self.ZERO_POINT_TYPES:
                info_breakdown.append({
                    "issue_type": issue_type,
                    "category": "Reference Status",
                    "title": issue.get("title", issue_type),
                    "severity": "Info",
                    "points_added": 0,
                    "expected": issue.get("expected", ""),
                    "found": issue.get("found", ""),
                    "description": issue.get("description", "")
                })
            elif issue_type in self.INCONSISTENCY_WEIGHTS:
                pts = self.INCONSISTENCY_WEIGHTS[issue_type]
                inconsistency_score += pts
                inconsistency_breakdown.append({
                    "issue_type": issue_type,
                    "category": "Record Inconsistency",
                    "title": issue.get("title", issue_type),
                    "severity": issue.get("severity", "High"),
                    "points_added": pts,
                    "expected": issue.get("expected", ""),
                    "found": issue.get("found", ""),
                    "description": issue.get("description", "")
                })
            elif issue_type in self.DATA_QUALITY_WEIGHTS:
                pts = self.DATA_QUALITY_WEIGHTS[issue_type]
                quality_score += pts
                quality_breakdown.append({
                    "issue_type": issue_type,
                    "category": "Data Quality Warning",
                    "severity": issue.get("severity", "Medium"),
                    "points_added": pts,
                    "expected": issue.get("expected", ""),
                    "found": issue.get("found", ""),
                    "description": issue.get("description", "")
                })
            else:
                pts = 10
                inconsistency_score += pts
                inconsistency_breakdown.append({
                    "issue_type": issue_type,
                    "category": "Unclassified Warning",
                    "title": issue.get("title", issue_type),
                    "severity": "Medium",
                    "points_added": pts,
                    "description": issue.get("description", "")
                })

        raw_total_score = inconsistency_score + quality_score
        final_risk_score = min(raw_total_score, 100)

        # 3. Determine Risk Level Category
        risk_level = self.determine_risk_level(final_risk_score)

        # 4. Generate Recommendation
        recommendation = self.generate_recommendation(
            risk_level=risk_level,
            ver_status=ver_status,
            inconsistencies_count=len(inconsistency_breakdown),
            quality_warnings_count=len(quality_breakdown)
        )

        all_scoring_breakdown = inconsistency_breakdown + quality_breakdown + info_breakdown

        # 5. Persist Assessment in PostgreSQL risk_assessments Table
        assessment_id = f"RSK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        summary_str = "; ".join([f"{item['title']} (+{item['points_added']} pts)" for item in all_scoring_breakdown]) or "No anomalies detected."

        risk_db = RiskAssessment(
            assessment_id=assessment_id,
            verification_id=verification_id,
            risk_score=final_risk_score,
            risk_level=risk_level,
            ownership_continuity_score=sum(i["points_added"] for i in inconsistency_breakdown if "OWNER" in i["issue_type"] or "HISTORY" in i["issue_type"]),
            area_discrepancy_score=sum(i["points_added"] for i in inconsistency_breakdown if "AREA" in i["issue_type"]),
            encumbrance_score=sum(i["points_added"] for i in inconsistency_breakdown if "DUPLICATE" in i["issue_type"] or "SURVEY" in i["issue_type"]),
            recommendations=f"{recommendation} | Summary: {summary_str}"
        )

        try:
            db.query(RiskAssessment).filter(RiskAssessment.verification_id == verification_id).delete()
            db.add(risk_db)
            db.commit()
        except Exception as err:
            try:
                db.rollback()
            except Exception:
                pass
            print(f"Notice: Risk assessment DB persistence note: {err}")

        return {
            "assessment_id": assessment_id,
            "document_id": document_id,
            "verification_id": verification_id,
            "verification_status": ver_status,
            "risk_score": final_risk_score,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "inconsistency_score": inconsistency_score,
            "quality_score": quality_score,
            "record_inconsistencies": inconsistency_breakdown,
            "data_quality_warnings": quality_breakdown,
            "reference_notices": info_breakdown,
            "scoring_breakdown": all_scoring_breakdown,
            "total_anomalies_count": len(all_scoring_breakdown),
            "matched_land_record": verification_payload.get("matched_land_record"),
            "disclaimer": "Student prototype / demonstration risk scoring engine. Not a substitute for authorized legal or government title search."
        }

    def determine_risk_level(self, score: int) -> str:
        """
        Assigns standard risk level category:
        0–29: LOW
        30–59: MEDIUM
        60–79: HIGH
        80–100: CRITICAL
        """
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 30:
            return "MEDIUM"
        return "LOW"

    def generate_recommendation(
        self,
        risk_level: str,
        ver_status: str = "VERIFIED",
        inconsistencies_count: int = 0,
        quality_warnings_count: int = 0
    ) -> str:
        """
        Generates responsible, evidence-based recommendations without unsupported claims of fraud.
        """
        if ver_status == "REFERENCE_NOT_FOUND":
            return "Unindexed parcel in demonstration registry: Manual physical inspection and registry verification recommended."

        if risk_level == "CRITICAL":
            return "Immediate detailed verification required"
        elif risk_level == "HIGH":
            return "Further verification required"
        elif risk_level == "MEDIUM":
            return "Manual review recommended"
        else:
            return "No major inconsistency detected"


# Singleton export
risk_scoring_engine = ExplainableRiskScoringEngine()
