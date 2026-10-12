from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DocumentRecord, RiskAssessment, VerificationResult
from app.risk_scoring.engine import risk_scoring_engine

router = APIRouter()


@router.post("/assess/{document_id}", status_code=status.HTTP_200_OK)
def assess_document_risk(document_id: str, db: Session = Depends(get_db)):
    """
    Run explainable risk scoring assessment for a document_id.
    Generates a 0-100 risk score, risk level (LOW/MEDIUM/HIGH/CRITICAL),
    transparent point breakdown, and revenue recommendation.
    """
    doc_record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
    if not doc_record:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID '{document_id}' not found in database."
        )

    risk_payload = risk_scoring_engine.compute_risk_assessment(document_id, db)
    return risk_payload


@router.get("/assessment/{document_id}")
def get_risk_assessment_result(document_id: str, db: Session = Depends(get_db)):
    """
    Fetch computed risk assessment breakdown and recommendations for a document_id.
    """
    doc_record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
    if not doc_record:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID '{document_id}' not found in database."
        )

    return risk_scoring_engine.compute_risk_assessment(document_id, db)
