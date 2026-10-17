"""Dashboard data read from the active database and imported parcel files."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.gis.spatial_engine import gis_spatial_engine
from app.models import DocumentRecord, LandRecord, OwnershipHistory, RiskAssessment, VerificationResult

router = APIRouter()


@router.get("")
def get_dashboard(db: Session = Depends(get_db)):
    # Select only the latest persisted result per document. Never manufacture a
    # verification outcome from the fact that a registry record was imported.
    verifications = {}
    for result in db.query(VerificationResult).order_by(
        VerificationResult.verification_timestamp.desc(), VerificationResult.verification_id.desc()
    ).all():
        verifications.setdefault(result.document_id, result)
    assessments = {}
    for result in db.query(RiskAssessment).order_by(
        RiskAssessment.assessed_at.desc(), RiskAssessment.assessment_id.desc()
    ).all():
        assessments.setdefault(result.verification_id, result)
    scores = [assessments[v.verification_id].risk_score for v in verifications.values()
              if v.verification_id in assessments]
    stats = {
        "land_records": db.query(LandRecord).count(),
        "ownership_history": db.query(OwnershipHistory).count(),
        "parcels": len(gis_spatial_engine.geojson_data.get("features", [])),
        "uploaded_documents": db.query(DocumentRecord).count(),
        "checked_documents": len(verifications),
        "verified_documents": sum(v.verification_status == "VERIFIED" for v in verifications.values()),
        "suspicious_documents": sum(v.verification_status == "SUSPICIOUS" for v in verifications.values()),
        "average_risk_score": round(sum(scores) / len(scores), 1) if scores else None,
    }
    documents = []
    for doc in db.query(DocumentRecord).order_by(DocumentRecord.upload_timestamp.desc(), DocumentRecord.document_id.desc()).limit(10):
        verification = verifications.get(doc.document_id)
        assessment = assessments.get(verification.verification_id) if verification else None
        documents.append({
            "document_id": doc.document_id, "filename": doc.filename,
            "owner_name": doc.extracted_owner_name, "survey_number": doc.extracted_survey_number,
            "location": doc.extracted_location, "ocr_status": doc.ocr_status,
            "verification_status": verification.verification_status if verification else "NOT_CHECKED",
            "risk_score": assessment.risk_score if assessment else None,
        })
    records = [{
        "record_id": r.record_id, "owner_name": r.owner_name, "survey_number": r.survey_number,
        "land_area_acres": float(r.land_area_acres), "village": r.village, "district": r.district,
    } for r in db.query(LandRecord).order_by(LandRecord.record_id).limit(12)]
    return {"database_engine": db.get_bind().dialect.name, "stats": stats,
            "recent_documents": documents, "registry_preview": records}
