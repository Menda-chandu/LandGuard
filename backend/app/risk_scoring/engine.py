import uuid
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from app.models import RiskAssessment, VerificationResult, DocumentRecord
from app.verification.engine import verification_engine
from app.risk_scoring.ml import assess_reference_outlier


class ExplainableRiskScoringEngine:
    """
    Transparent, Rule-Based Explainable Risk Scoring Engine for LandGuard.
    Calculates a fraud risk index from 0 to 100 based on weighted anomalies
    detected during land record verification.
    """

    def __init__(self):
        # Explicit Rule Weights
        self.ANOMALY_WEIGHTS = {
            "OWNER_NAME_MISMATCH": 25,
            "SURVEY_NUMBER_MISMATCH": 25,
            "SURVEY_NOT_FOUND": 25,
            "LAND_AREA_MISMATCH": 20,
            "DUPLICATE_REGISTRATION_FLAGGED": 30,
            "RAPID_OWNERSHIP_TRANSFER": 15,
            "UNFOUND_SELLER_IN_HISTORY": 15,
            "UNFOUNDED_SELLER_IN_HISTORY": 15,
            "MISSING_HISTORICAL_TITLE_CHAIN": 15,
            "INCOMPLETE_DOCUMENT_DATA": 10,
            "DOCUMENT_NOT_FOUND": 30,
            "SPATIAL_LOCATION_MISMATCH": 20,
            "GIS_PARCEL_NOT_FOUND": 15,
            "REGISTRATION_NUMBER_MISMATCH": 25,
            "REGISTRATION_DATE_MISMATCH": 15,
            "DUPLICATE_DOCUMENT": 10,
            "BOUNDARY_DESCRIPTION_MISMATCH": 20,
            "BOUNDARY_GEOMETRY_MISMATCH": 25,
            "PARCEL_ENCROACHMENT": 25,
        }

    def compute_risk_assessment(self, document_id: str, db: Session) -> Dict[str, Any]:
        """
        Computes risk score and level for a given document_id, persists the result
        in PostgreSQL risk_assessments table, and returns an explainable breakdown.
        """
        # 1. Run or fetch verification results for document
        verification_payload = verification_engine.verify_document(document_id, db)
        verification_id = verification_payload.get("verification_id", f"VER-{document_id}")
        detected_anomalies = verification_payload.get("detected_anomalies", [])

        # 2. Compute Risk Score & Scoring Breakdown
        scoring_breakdown = []
        raw_score = 0

        for anomaly in detected_anomalies:
            anom_type = anomaly.get("type", "UNKNOWN")
            pts = self.ANOMALY_WEIGHTS.get(anom_type, 10)
            raw_score += pts

            scoring_breakdown.append({
                "anomaly_type": anom_type,
                "title": anomaly.get("title", anom_type),
                "severity": anomaly.get("severity", "Medium"),
                "points_added": pts,
                "expected": anomaly.get("expected", ""),
                "found": anomaly.get("found", ""),
                "description": anomaly.get("description", "")
            })

        from app.models import DocumentRecord
        document = db.query(DocumentRecord).filter_by(document_id=document_id).first()
        ml_assessment = assess_reference_outlier(db, verification_payload.get("matched_land_record"), document.extracted_land_area if document else None)
        if ml_assessment["risk_points"]:
            raw_score += ml_assessment["risk_points"]
            scoring_breakdown.append({"anomaly_type": "ML_REFERENCE_OUTLIER", "title": "Unusual Parcel Compared With Reference Data", "severity": "Medium",
                                      "points_added": ml_assessment["risk_points"],
                                      "description": f"Isolation Forest ranks this parcel at outlier percentile {ml_assessment['outlier_percentile']}. This is an advisory statistical signal, not a fraud finding."})

        # Cap score at 100
        final_risk_score = min(raw_score, 100)

        # 3. Determine Risk Level Category
        risk_level = self.determine_risk_level(final_risk_score)

        # 4. Generate Recommendation
        recommendation = self.generate_recommendation(risk_level)
        if risk_level == "LOW" and detected_anomalies:
            recommendation = "Manual review recommended for flagged inconsistencies"

        # 5. Persist Assessment in PostgreSQL risk_assessments Table
        assessment_id = f"RSK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        summary_str = "; ".join([f"{item['title']} (+{item['points_added']} pts)" for item in scoring_breakdown]) or "No anomalies detected."

        risk_db = RiskAssessment(
            assessment_id=assessment_id,
            verification_id=verification_id,
            risk_score=final_risk_score,
            risk_level=risk_level,
            ownership_continuity_score=sum(i["points_added"] for i in scoring_breakdown if "OWNER" in i["anomaly_type"] or "HISTORY" in i["anomaly_type"]),
            area_discrepancy_score=sum(i["points_added"] for i in scoring_breakdown if "AREA" in i["anomaly_type"]),
            encumbrance_score=sum(i["points_added"] for i in scoring_breakdown if "DUPLICATE" in i["anomaly_type"] or "SURVEY" in i["anomaly_type"]),
            recommendations=f"{recommendation} | Summary: {summary_str}"
        )

        try:
            # Clear existing risk assessment for this verification_id if present
            db.query(RiskAssessment).filter(RiskAssessment.verification_id == verification_id).delete()
            db.add(risk_db)
            db.commit()
        except Exception as err:
            try:
                db.rollback()
            except Exception:
                pass
            raise RuntimeError("Database could not persist the risk assessment") from err

        return {
            "assessment_id": assessment_id,
            "document_id": document_id,
            "verification_id": verification_id,
            "risk_score": final_risk_score,
            "risk_level": risk_level,
            "verification_status": verification_payload.get("verification_status"),
            "ml_assessment": ml_assessment,
            "evidence_checks": verification_payload.get("evidence_checks", {}),
            "recommendation": recommendation,
            "total_anomalies_count": len(scoring_breakdown),
            "scoring_breakdown": scoring_breakdown,
            "matched_land_record": verification_payload.get("matched_land_record")
        }

    def determine_risk_level(self, score: int) -> str:
        """
        Assigns risk level category:
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
        else:
            return "LOW"

    def generate_recommendation(self, risk_level: str) -> str:
        """
        Generates verification action guidelines.
        """
        if risk_level == "LOW":
            return "No major inconsistency detected"
        elif risk_level == "MEDIUM":
            return "Manual review recommended"
        elif risk_level == "HIGH":
            return "Further verification required"
        else:
            return "Immediate detailed verification required"


# Singleton Export
risk_scoring_engine = ExplainableRiskScoringEngine()
