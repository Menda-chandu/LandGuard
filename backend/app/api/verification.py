import os
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VerificationResult, DocumentRecord
from app.verification.engine import verification_engine
from app.api.documents import UPLOADS_DIR

logger = logging.getLogger("landguard.verification")

router = APIRouter()


@router.post("/verify/{document_id}", status_code=status.HTTP_200_OK)
def verify_document_endpoint(document_id: str, db: Session = Depends(get_db)):
    """
    Run land record verification and anomaly detection for a given document_id.
    Cross-matches extracted NLP attributes against revenue records and ownership history chains.
    """
    doc_record = None
    try:
        doc_record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
    except Exception as e:
        logger.warning(f"Notice: Database query for verification '{document_id}': {e}")
        try:
            db.rollback()
        except Exception:
            pass

    if not doc_record:
        matching_files = [f for f in os.listdir(UPLOADS_DIR) if f.startswith(document_id)] if os.path.exists(UPLOADS_DIR) else []
        if not matching_files:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID '{document_id}' not found in database or uploads storage."
            )

    verification_result = verification_engine.verify_document(document_id, db)
    return verification_result


@router.get("/results/{document_id}")
def get_verification_results(document_id: str, db: Session = Depends(get_db)):
    """
    Fetch stored verification results and anomaly audit breakdown for a document_id.
    """
    ver_record = None
    try:
        ver_record = db.query(VerificationResult).filter(VerificationResult.document_id == document_id).first()
    except Exception as e:
        logger.warning(f"Notice: Database query for verification results '{document_id}': {e}")
        try:
            db.rollback()
        except Exception:
            pass

    if not ver_record:
        doc_record = None
        try:
            doc_record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass

        if not doc_record:
            matching_files = [f for f in os.listdir(UPLOADS_DIR) if f.startswith(document_id)] if os.path.exists(UPLOADS_DIR) else []
            if not matching_files:
                raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    return verification_engine.verify_document(document_id, db)
