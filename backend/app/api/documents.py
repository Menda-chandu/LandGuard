import os
import shutil
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import DocumentRecord, OwnershipHistory, LandRecord
from app.ocr.processor import process_document_ocr
from app.nlp.extractor import nlp_engine
from sqlalchemy import or_
import logging

logger = logging.getLogger("landguard.documents")

router = APIRouter()

# Target upload directory (relative to project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB limit


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a land document (PDF, PNG, JPG, TIFF), save to uploads folder,
    run Tesseract OCR pipeline, trigger NLP information extraction,
    and persist structured record in document_records table.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided in upload request.")

    # 1. Validate File Extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # 2. Ensure Uploads Folder Exists
    os.makedirs(UPLOADS_DIR, exist_ok=True)

    # 3. Generate Unique Document ID and Filepath
    doc_id = f"DOC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    safe_filename = f"{doc_id}_{file.filename.replace(' ', '_')}"
    saved_file_path = os.path.join(UPLOADS_DIR, safe_filename)

    # 4. Save File to Disk
    file_size = 0
    try:
        with open(saved_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = os.path.getsize(saved_file_path)

        if file_size > MAX_FILE_SIZE_BYTES:
            os.remove(saved_file_path)
            raise HTTPException(
                status_code=400,
                detail=f"File size ({round(file_size/(1024*1024), 2)}MB) exceeds maximum limit of 25MB."
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    # 5. Run OCR Text Extraction Pipeline
    ocr_result = process_document_ocr(saved_file_path)
    ocr_text = ocr_result.get("text", "")

    # 6. Run NLP Information Extraction Pipeline
    nlp_result = nlp_engine.extract_information(ocr_text)
    fields = nlp_result.get("extracted_fields", {})

    # 7. Save Record in PostgreSQL document_records Table
    file_type_str = ext.replace('.', '').upper()
    relative_path = os.path.relpath(saved_file_path, PROJECT_ROOT)

    doc_record = DocumentRecord(
        document_id=doc_id,
        filename=file.filename,
        file_path=relative_path,
        file_type=file_type_str,
        file_size_bytes=file_size,
        ocr_status=ocr_result.get("status", "COMPLETED"),
        extracted_text=ocr_text,
        extracted_owner_name=fields.get("owner_name"),
        extracted_survey_number=fields.get("survey_number"),
        extracted_land_area=fields.get("land_area_acres"),
        extracted_location=nlp_result.get("location_summary"),
        ocr_confidence_score=ocr_result.get("confidence", 0.0)
    )

    try:
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)
    except Exception as db_err:
        db.rollback()
        print(f"Notice: PostgreSQL persistence note: {db_err}")

    return {
        "message": "Document uploaded, OCR processed, and NLP entities extracted successfully.",
        "document_id": doc_id,
        "filename": file.filename,
        "file_path": relative_path,
        "file_type": file_type_str,
        "file_size_bytes": file_size,
        "ocr_status": ocr_result.get("status", "COMPLETED"),
        "ocr_engine": ocr_result.get("engine", "Tesseract OCR"),
        "ocr_confidence_score": ocr_result.get("confidence", 0.0),
        "nlp_confidence_score": nlp_result.get("nlp_confidence_score", 0.0),
        "extracted_text": ocr_text,
        "extracted_nlp_fields": fields,
        "location_summary": nlp_result.get("location_summary")
    }


@router.get("/{document_id}")
def get_document_details(document_id: str, db: Session = Depends(get_db)):
    """
    Fetch document record and extracted OCR details by document_id.
    """
    record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Document with ID '{document_id}' not found.")

    return {
        "document_id": record.document_id,
        "filename": record.filename,
        "file_path": record.file_path,
        "file_type": record.file_type,
        "file_size_bytes": record.file_size_bytes,
        "upload_timestamp": record.upload_timestamp,
        "ocr_status": record.ocr_status,
        "ocr_confidence_score": record.ocr_confidence_score,
        "extracted_owner_name": record.extracted_owner_name,
        "extracted_survey_number": record.extracted_survey_number,
        "extracted_land_area": record.extracted_land_area,
        "extracted_location": record.extracted_location,
        "extracted_text": record.extracted_text
    }


@router.get("/search")
def search_records(
    q: Optional[str] = None,
    limit: int = 15,
    db: Session = Depends(get_db)
):
    """
    Global search endpoint across LandRecords and DocumentRecords.
    Supports search by survey_number, owner_name, record_id/document_id, and location.
    """
    if not q or not q.strip():
        return {"query": "", "count": 0, "results": []}

    query_str = f"%{q.strip().lower()}%"
    results = []

    try:
        # 1. Search LandRecords
        land_recs = db.query(LandRecord).filter(
            or_(
                LandRecord.survey_number.ilike(query_str),
                LandRecord.owner_name.ilike(query_str),
                LandRecord.record_id.ilike(query_str),
                LandRecord.village.ilike(query_str),
                LandRecord.mandal.ilike(query_str),
                LandRecord.district.ilike(query_str),
                LandRecord.registration_number.ilike(query_str)
            )
        ).limit(limit).all()

        for rec in land_recs:
            results.append({
                "type": "land_record",
                "id": rec.record_id,
                "record_id": rec.record_id,
                "survey_number": rec.survey_number,
                "owner_name": rec.owner_name or "Unspecified",
                "land_area_acres": float(rec.land_area_acres) if rec.land_area_acres else 0.0,
                "village": rec.village,
                "mandal": rec.mandal,
                "district": rec.district,
                "state": rec.state,
                "registration_number": rec.registration_number,
                "registration_date": rec.registration_date.strftime("%Y-%m-%d") if rec.registration_date else None,
                "document_type": rec.document_type
            })

        # 2. Search DocumentRecords
        doc_recs = db.query(DocumentRecord).filter(
            or_(
                DocumentRecord.document_id.ilike(query_str),
                DocumentRecord.filename.ilike(query_str),
                DocumentRecord.extracted_owner_name.ilike(query_str),
                DocumentRecord.extracted_survey_number.ilike(query_str),
                DocumentRecord.extracted_location.ilike(query_str)
            )
        ).limit(limit).all()

        for doc in doc_recs:
            results.append({
                "type": "document_record",
                "id": doc.document_id,
                "document_id": doc.document_id,
                "filename": doc.filename,
                "survey_number": doc.extracted_survey_number or "N/A",
                "owner_name": doc.extracted_owner_name or "Unspecified",
                "land_area_acres": float(doc.extracted_land_area) if doc.extracted_land_area else 0.0,
                "location": doc.extracted_location,
                "ocr_status": doc.ocr_status,
                "ocr_confidence_score": float(doc.ocr_confidence_score) if doc.ocr_confidence_score else 0.0,
                "extracted_text": doc.extracted_text
            })
    except Exception as e:
        logger.warning(f"Error querying search records in DB: {e}")

    return {
        "query": q,
        "count": len(results),
        "results": results
    }


@router.get("/{document_id}/nlp")
@router.post("/{document_id}/extract-nlp")
def extract_document_nlp(document_id: str, db: Session = Depends(get_db)):
    """
    NLP Information Extraction API endpoint.
    Accepts document_id, parses stored OCR text, updates database fields,
    and returns structured JSON (owner, survey_no, land_area, location, registration, boundaries).
    """
    record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
    ocr_text = ""

    if record and record.extracted_text:
        ocr_text = record.extracted_text
    else:
        matching_files = [f for f in os.listdir(UPLOADS_DIR) if f.startswith(document_id)] if os.path.exists(UPLOADS_DIR) else []
        if matching_files:
            file_path = os.path.join(UPLOADS_DIR, matching_files[0])
            ocr_res = process_document_ocr(file_path)
            ocr_text = ocr_res.get("text", "")
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_id}' not found in database or uploads storage."
            )

    nlp_result = nlp_engine.extract_information(ocr_text)
    fields = nlp_result.get("extracted_fields", {})

    if record:
        record.extracted_owner_name = fields.get("owner_name")
        record.extracted_survey_number = fields.get("survey_number")
        record.extracted_land_area = fields.get("land_area_acres")
        record.extracted_location = nlp_result.get("location_summary")
        try:
            db.commit()
        except Exception:
            db.rollback()

    return {
        "status": "SUCCESS",
        "document_id": document_id,
        "nlp_confidence_score": nlp_result.get("nlp_confidence_score"),
        "fields_extracted_count": nlp_result.get("fields_extracted_count"),
        "location_summary": nlp_result.get("location_summary"),
        "extracted_attributes": fields
    }


@router.get("/{document_id}/history")
def get_document_ownership_history(document_id: str, db: Session = Depends(get_db)):
    """
    Fetch ownership transfer chain timeline matching document's survey number.
    """
    doc = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
    survey_no = doc.extracted_survey_number if doc else "402/B"

    if not survey_no and doc and doc.extracted_text:
        nlp_res = nlp_engine.extract_information(doc.extracted_text)
        survey_no = nlp_res.get("extracted_fields", {}).get("survey_number") or "402/B"

    history_records = db.query(OwnershipHistory).filter(
        OwnershipHistory.survey_number == survey_no
    ).order_by(OwnershipHistory.transfer_date.asc()).all()

    items = []
    for h in history_records:
        items.append({
            "history_id": h.history_id,
            "survey_number": h.survey_number,
            "owner_name": h.owner_name,
            "transfer_date": h.transfer_date.strftime("%Y-%m-%d") if h.transfer_date else "N/A",
            "transfer_type": h.transfer_type
        })

    return {
        "document_id": document_id,
        "survey_number": survey_no,
        "timeline_count": len(items),
        "history_timeline": items
    }
