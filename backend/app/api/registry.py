"""Read reference registry entries separately from uploaded documents."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import LandRecord, OwnershipHistory

router = APIRouter()


@router.get("/{record_id}")
def get_registry_record(record_id: str, db: Session = Depends(get_db)):
    record = db.get(LandRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Land registry record not found.")
    history = db.query(OwnershipHistory).filter(
        OwnershipHistory.survey_number == record.survey_number
    ).order_by(OwnershipHistory.transfer_date.asc()).all()
    return {
        "record_id": record.record_id, "owner_name": record.owner_name,
        "survey_number": record.survey_number, "land_area_acres": float(record.land_area_acres),
        "village": record.village, "mandal": record.mandal, "district": record.district,
        "state": record.state, "document_type": record.document_type,
        "registration_number": record.registration_number, "registration_date": record.registration_date,
        "history_timeline": [{"history_id": item.history_id, "owner_name": item.owner_name,
                              "transfer_date": item.transfer_date, "transfer_type": item.transfer_type}
                             for item in history],
    }
