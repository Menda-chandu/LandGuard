import uuid
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from app.models import RiskAssessment, VerificationResult, DocumentRecord
from app.verification.engine import verification_engine


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
            "DOCUMENT_NOT_FOUND": 30
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

        # Cap score at 100
        final_risk_score = min(raw_score, 100)

        # 3. Determine Risk Level Category
        risk_level = self.determine_risk_level(final_risk_score)

        # 4. Generate Recommendation
        recommendation = self.generate_recommendation(risk_level)

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
            print(f"Notice: Risk assessment DB persistence note: {err}")

        return {
            "assessment_id": assessment_id,
            "document_id": document_id,
            "verification_id": verification_id,
            "risk_score": final_risk_score,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "total_anomalies_count": len(detected_anomalies),
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
