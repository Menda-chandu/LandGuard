import os
import mimetypes
import uuid
import json
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status, Query, Body
from fastapi.responses import FileResponse, Response
from urllib.parse import quote
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import DocumentRecord, DocumentFile, OwnershipHistory, LandRecord
from app.ocr.processor import process_document_ocr
from app.nlp.extractor import nlp_engine
from app.config import settings
from app.document_processing.fingerprints import file_fingerprint, text_fingerprint
from app.gis.boundaries import validate_geometry
from sqlalchemy import or_, func
import logging

logger = logging.getLogger("landguard.documents")

router = APIRouter()

# Target upload directory (relative to project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB limit
SAMPLE_FILES = {
    "LandGuard_Synthetic_Test_Land_Record.pdf": "Digital test deed",
    "ocr_test_synthetic_deed.png": "Scanned synthetic deed",
    "ocr_test_synthetic_deed.jpg": "Scanned synthetic deed (JPEG)",
    "sample_deed.png": "Sample deed scan",
    "test_synth_deed.png": "Additional test scan",
    "pahani_demo.pdf": "Synthetic English Pahani record",
    "pahani_demo.png": "Synthetic English Pahani scan",
}


@router.get("/samples")
def list_sample_documents():
    return {"samples": [
        {"name": name, "description": description, "size_bytes": path.stat().st_size}
        for name, description in SAMPLE_FILES.items()
        if (path := settings.DATASET_DIR / name).is_file()
    ]}


@router.get("/samples/{filename}")
def get_sample_document(filename: str):
    if filename not in SAMPLE_FILES:
        raise HTTPException(status_code=404, detail="Sample document not found.")
    path = settings.DATASET_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Sample document not found.")
    return FileResponse(path, filename=filename)


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
    original_name = os.path.basename(file.filename.replace("\\", "/"))
    safe_filename = f"{doc_id}_{original_name.replace(' ', '_')}"
    saved_file_path = os.path.join(UPLOADS_DIR, safe_filename)

    # 4. Save File to Disk
    file_size = 0
    try:
        with open(saved_file_path, "wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE_BYTES:
                    raise HTTPException(status_code=413, detail="File exceeds the maximum size of 25 MB.")
                buffer.write(chunk)
    except HTTPException:
        os.remove(saved_file_path)
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
        ocr_confidence_score=ocr_result.get("confidence", 0.0),
        content_sha256=file_fingerprint(saved_file_path),
        text_sha256=text_fingerprint(ocr_text) if ocr_result.get("status") == "COMPLETED" else None,
    )

    try:
        db.add(doc_record)
        db.flush()
        db.add(DocumentFile(document_id=doc_id, content=Path(saved_file_path).read_bytes(),
                            media_type=mimetypes.guess_type(original_name)[0] or "application/octet-stream"))
        db.commit()
        db.refresh(doc_record)
    except Exception as db_err:
        db.rollback()
        os.remove(saved_file_path)
        logger.exception("Document could not be saved")
        raise HTTPException(status_code=503, detail="Database could not save the document. Please retry when the database is available.") from db_err

    duplicate_filters = [DocumentRecord.content_sha256 == doc_record.content_sha256]
    if doc_record.text_sha256:
        duplicate_filters.append(DocumentRecord.text_sha256 == doc_record.text_sha256)
    duplicates = db.query(DocumentRecord).filter(DocumentRecord.document_id != doc_id, or_(*duplicate_filters)).all()
    if not settings.KEEP_LOCAL_UPLOADS:
        os.remove(saved_file_path)

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
        "location_summary": nlp_result.get("location_summary"),
        "duplicate_documents": [{"document_id": d.document_id, "evidence": "IDENTICAL_FILE" if d.content_sha256 == doc_record.content_sha256 else "IDENTICAL_NORMALIZED_TEXT"} for d in duplicates],
    }


@router.get("/search")
def search_records(
    q: Optional[str] = None,
    limit: int = Query(15, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Global search endpoint across LandRecords and DocumentRecords.
    Supports search by survey_number, owner_name, record_id/document_id, and location.
    """
    if not q or not q.strip():
        return {"query": "", "count": 0, "results": []}

    query_str = f"%{q.strip().lower()}%"
    compact_query = q.strip().lower().replace("/", "").replace("-", "").replace(" ", "")
    def compact(column):
        return func.replace(func.replace(func.replace(func.lower(column), "/", ""), "-", ""), " ", "")
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
                LandRecord.registration_number.ilike(query_str),
                compact(LandRecord.survey_number).contains(compact_query),
                compact(LandRecord.record_id).contains(compact_query)
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
                DocumentRecord.extracted_location.ilike(query_str),
                compact(DocumentRecord.document_id).contains(compact_query),
                compact(DocumentRecord.extracted_survey_number).contains(compact_query)
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


@router.get("/{document_id}")
def get_document_details(document_id: str, db: Session = Depends(get_db)):
    """
    Fetch document record and extracted OCR details by document_id.
    """
    record = None
    try:
        record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
    except Exception as e:
        logger.warning(f"Notice: Database query for document '{document_id}': {e}")
        try:
            db.rollback()
        except Exception:
            pass

    if not record:
        matching_files = [f for f in os.listdir(UPLOADS_DIR) if f.startswith(document_id)] if os.path.exists(UPLOADS_DIR) else []
        if matching_files:
            file_path = os.path.join(UPLOADS_DIR, matching_files[0])
            ocr_res = process_document_ocr(file_path)
            ocr_text = ocr_res.get("text", "")
            nlp_res = nlp_engine.extract_information(ocr_text)
            fields = nlp_res.get("extracted_fields", {})
            return {
                "document_id": document_id,
                "filename": matching_files[0],
                "file_path": os.path.relpath(file_path, PROJECT_ROOT),
                "file_type": os.path.splitext(matching_files[0])[1].replace(".", "").upper(),
                "file_size_bytes": os.path.getsize(file_path),
                "upload_timestamp": datetime.now().isoformat(),
                "ocr_status": ocr_res.get("status", "COMPLETED"),
                "ocr_confidence_score": float(ocr_res.get("confidence", 0.0)),
                "extracted_owner_name": fields.get("owner_name"),
                "extracted_survey_number": fields.get("survey_number"),
                "extracted_land_area": fields.get("land_area_acres"),
                "extracted_location": nlp_res.get("location_summary"),
                "extracted_text": ocr_text
            }
        raise HTTPException(status_code=404, detail=f"Document with ID '{document_id}' not found.")

    return {
        "document_id": record.document_id,
        "filename": record.filename,
        "file_path": record.file_path,
        "file_type": record.file_type,
        "file_size_bytes": record.file_size_bytes,
        "upload_timestamp": record.upload_timestamp,
        "ocr_status": record.ocr_status,
        "ocr_confidence_score": float(record.ocr_confidence_score) if record.ocr_confidence_score else 0.0,
        "extracted_owner_name": record.extracted_owner_name,
        "extracted_survey_number": record.extracted_survey_number,
        "extracted_land_area": float(record.extracted_land_area) if record.extracted_land_area else 0.0,
        "extracted_location": record.extracted_location,
        "extracted_text": record.extracted_text,
        "extracted_nlp_fields": nlp_engine.extract_information(record.extracted_text or "").get("extracted_fields", {}),
        "claimed_geometry": json.loads(record.claimed_geometry) if record.claimed_geometry else None,
    }


@router.put("/{document_id}/boundary")
def set_document_boundary(document_id: str, geometry: dict = Body(...), db: Session = Depends(get_db)):
    """Attach a surveyed WGS84 GeoJSON claim and immediately recheck the document."""
    record = db.query(DocumentRecord).filter_by(document_id=document_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Upload a document before attaching its boundary.")
    try:
        validated = validate_geometry(geometry)
    except (ValueError, TypeError, KeyError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    record.claimed_geometry = json.dumps(validated)
    db.commit()
    from app.verification.engine import verification_engine
    return verification_engine.verify_document(document_id, db)


@router.get("/{document_id}/file")
def download_document_file(document_id: str, db: Session = Depends(get_db)):
    record = db.get(DocumentRecord, document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    stored = db.get(DocumentFile, document_id)
    if stored:
        return Response(content=stored.content, media_type=stored.media_type,
                        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(record.filename, safe='')}"})
    path = (Path(PROJECT_ROOT) / record.file_path).resolve()
    if path.is_relative_to(Path(UPLOADS_DIR).resolve()) and path.is_file():
        return FileResponse(path, filename=record.filename)
    raise HTTPException(status_code=404, detail="Original file is unavailable for this older upload.")


@router.get("/{document_id}/nlp")
@router.post("/{document_id}/extract-nlp")
def extract_document_nlp(document_id: str, db: Session = Depends(get_db)):
    """
    NLP Information Extraction API endpoint.
    Accepts document_id, parses stored OCR text, updates database fields,
    and returns structured JSON (owner, survey_no, land_area, location, registration, boundaries).
    """
    record = None
    try:
        record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
    except Exception as e:
        logger.warning(f"Notice: Database query for document '{document_id}': {e}")
        try:
            db.rollback()
        except Exception:
            pass

    ocr_text = ""
    ocr_confidence = 0.0

    if record and record.extracted_text:
        ocr_text = record.extracted_text
        ocr_confidence = float(record.ocr_confidence_score) if record.ocr_confidence_score else 0.0
    else:
        matching_files = [f for f in os.listdir(UPLOADS_DIR) if f.startswith(document_id)] if os.path.exists(UPLOADS_DIR) else []
        if matching_files:
            file_path = os.path.join(UPLOADS_DIR, matching_files[0])
            ocr_res = process_document_ocr(file_path)
            ocr_text = ocr_res.get("text", "")
            ocr_confidence = float(ocr_res.get("confidence", 0.0))
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
            try:
                db.rollback()
            except Exception:
                pass

    return {
        "status": "SUCCESS",
        "document_id": document_id,
        "ocr_confidence_score": ocr_confidence,
        "extracted_text": ocr_text,
        "nlp_confidence_score": nlp_result.get("nlp_confidence_score", 0.0),
        "fields_extracted_count": nlp_result.get("fields_extracted_count", 0),
        "location_summary": nlp_result.get("location_summary"),
        "extracted_attributes": fields
    }


@router.get("/{document_id}/history")
def get_document_ownership_history(document_id: str, db: Session = Depends(get_db)):
    """
    Fetch ownership transfer chain timeline matching document's survey number.
    """
    doc = None
    try:
        doc = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
    except Exception as e:
        logger.warning(f"Notice: Database query for document history '{document_id}': {e}")
        try:
            db.rollback()
        except Exception:
            pass

    survey_no = doc.extracted_survey_number if doc else None

    if not survey_no and doc and doc.extracted_text:
        nlp_res = nlp_engine.extract_information(doc.extracted_text)
        survey_no = nlp_res.get("extracted_fields", {}).get("survey_number")

    if not survey_no:
        matching_files = [f for f in os.listdir(UPLOADS_DIR) if f.startswith(document_id)] if os.path.exists(UPLOADS_DIR) else []
        if matching_files:
            file_path = os.path.join(UPLOADS_DIR, matching_files[0])
            ocr_res = process_document_ocr(file_path)
            nlp_res = nlp_engine.extract_information(ocr_res.get("text", ""))
            survey_no = nlp_res.get("extracted_fields", {}).get("survey_number")

    history_records = []
    if survey_no:
        try:
            history_records = db.query(OwnershipHistory).filter(
                OwnershipHistory.survey_number == survey_no
            ).order_by(OwnershipHistory.transfer_date.asc()).all()
        except Exception as e:
            logger.warning(f"Notice: Ownership history query note: {e}")

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
