from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.gis.spatial_engine import gis_spatial_engine

router = APIRouter()


@router.get("/parcels")
def get_all_gis_parcels(db: Session = Depends(get_db)):
    """
    Returns GeoJSON FeatureCollection of all fictional land parcel polygon boundaries,
    enriched with live database attributes (owner_name, acreage, location, risk_level).
    """
    return gis_spatial_engine.get_all_parcels_geojson(db)


@router.get("/parcels/{survey_number:path}")
def get_gis_parcel_by_survey(survey_number: str, db: Session = Depends(get_db)):
    """
    Returns specific GeoJSON polygon feature and spatial metadata for a survey_number.
    """
    parcel_feature = gis_spatial_engine.get_parcel_by_survey(survey_number, db)
    if not parcel_feature:
        raise HTTPException(
            status_code=404,
            detail=f"GeoJSON GIS parcel polygon for Survey '{survey_number}' not found."
        )
    return parcel_feature


@router.post("/verify-spatial")
def verify_spatial_location_endpoint(
    survey_number: str,
    doc_village: Optional[str] = None,
    doc_mandal: Optional[str] = None,
    doc_district: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    GIS Spatial Location Verification Endpoint.
    Compares document location claims (village, mandal, district) against
    CAD GIS spatial polygon boundaries for the specified survey_number.
    """
    return gis_spatial_engine.verify_spatial_location(
        survey_number=survey_number,
        doc_village=doc_village,
        doc_mandal=doc_mandal,
        doc_district=doc_district,
        db=db
    )
