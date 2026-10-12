from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VerificationResult, DocumentRecord
from app.verification.engine import verification_engine

router = APIRouter()


@router.post("/verify/{document_id}", status_code=status.HTTP_200_OK)
def verify_document_endpoint(document_id: str, db: Session = Depends(get_db)):
    """
    Run land record verification and anomaly detection for a given document_id.
    Cross-matches extracted NLP attributes against revenue records and ownership history chains.
    """
    doc_record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
    if not doc_record:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID '{document_id}' not found in database."
        )

    verification_result = verification_engine.verify_document(document_id, db)
    return verification_result


@router.get("/results/{document_id}")
def get_verification_results(document_id: str, db: Session = Depends(get_db)):
    """
    Fetch stored verification results and anomaly audit breakdown for a document_id.
    """
    ver_record = db.query(VerificationResult).filter(VerificationResult.document_id == document_id).first()
    if not ver_record:
        # If not already verified, run verification now
        doc_record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
        if not doc_record:
            raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")
        return verification_engine.verify_document(document_id, db)

    # Re-run full structured payload
    return verification_engine.verify_document(document_id, db)
