import os
import json
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models import LandRecord, DocumentRecord

logger = logging.getLogger("landguard.gis")

# Path to sample GeoJSON file
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
GEOJSON_FILE_PATH = os.path.join(PROJECT_ROOT, "sample_data", "parcels.geojson")
SYNTHETIC_GEOJSON_FILE_PATH = os.path.join(PROJECT_ROOT, "sample_data", "parcels_synthetic_100.geojson")


class GISSpatialEngine:
    """
    GIS Spatial Engine for LandGuard.
    Handles GeoJSON parcel boundary mapping, spatial location verification,
    and GIS mismatch anomaly detection.
    """

    def __init__(self):
        self.geojson_data = self._load_sample_geojson()

    def _load_sample_geojson(self) -> Dict[str, Any]:
        combined_features = []
        if os.path.exists(GEOJSON_FILE_PATH):
            try:
                with open(GEOJSON_FILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    combined_features.extend(data.get("features", []))
            except Exception as e:
                logger.error(f"Failed to parse GeoJSON at {GEOJSON_FILE_PATH}: {e}")

        if os.path.exists(SYNTHETIC_GEOJSON_FILE_PATH):
            try:
                with open(SYNTHETIC_GEOJSON_FILE_PATH, "r", encoding="utf-8") as f:
                    syn_data = json.load(f)
                    combined_features.extend(syn_data.get("features", []))
            except Exception as e:
                logger.error(f"Failed to parse synthetic GeoJSON at {SYNTHETIC_GEOJSON_FILE_PATH}: {e}")

        return {"type": "FeatureCollection", "features": combined_features}

    def get_all_parcels_geojson(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Returns full GeoJSON FeatureCollection, enriching feature properties
        with live data from land_records database if available.
        """
        features = self.geojson_data.get("features", [])
        enriched_features = []

        for feature in features:
            props = feature.get("properties", {}).copy()
            survey_no = props.get("survey_number")

            if db and survey_no:
                try:
                    rec = db.query(LandRecord).filter(LandRecord.survey_number == survey_no).first()
                    if rec:
                        props["owner_name"] = rec.owner_name
                        props["land_area_acres"] = float(rec.land_area_acres)
                        props["village"] = rec.village
                        props["mandal"] = rec.mandal
                        props["district"] = rec.district
                except Exception as e:
                    logger.warning(f"Database enrichment error for survey {survey_no}: {e}")

            feature_copy = feature.copy()
            feature_copy["properties"] = props
            enriched_features.append(feature_copy)

        return {
            "type": "FeatureCollection",
            "name": "LandGuard_Spatial_Parcels",
            "features": enriched_features
        }

    def get_parcel_by_survey(self, survey_number: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single GeoJSON Feature by survey_number.
        """
        features = self.geojson_data.get("features", [])
        for feature in features:
            props = feature.get("properties", {})
            if props.get("survey_number") == survey_number:
                feature_copy = feature.copy()
                if db:
                    try:
                        rec = db.query(LandRecord).filter(LandRecord.survey_number == survey_number).first()
                        if rec:
                            feature_copy["properties"]["owner_name"] = rec.owner_name
                            feature_copy["properties"]["land_area_acres"] = float(rec.land_area_acres)
                            feature_copy["properties"]["village"] = rec.village
                            feature_copy["properties"]["mandal"] = rec.mandal
                            feature_copy["properties"]["district"] = rec.district
                    except Exception as e:
                        logger.warning(f"Database lookup error for survey {survey_number}: {e}")
                return feature_copy
        return None

    def verify_spatial_location(
        self,
        survey_number: Optional[str],
        doc_village: Optional[str] = None,
        doc_mandal: Optional[str] = None,
        doc_district: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Performs GIS Spatial Verification comparing document location claims
        against CAD polygon GIS boundary records.
        """
        anomalies: List[Dict[str, Any]] = []

        if not survey_number:
            anomalies.append({
                "type": "GIS_PARCEL_NOT_FOUND",
                "severity": "High",
                "title": "Missing Spatial Survey Key",
                "expected": "Valid Survey Number for GIS polygon lookup",
                "found": "Empty survey number",
                "description": "Spatial verification cannot proceed because survey parcel number is missing."
            })
            return {"spatial_match": False, "anomalies": anomalies}

        # 1. Lookup Parcel Geometry
        parcel_feature = self.get_parcel_by_survey(survey_number, db)

        if not parcel_feature:
            anomalies.append({
                "type": "GIS_PARCEL_NOT_FOUND",
                "severity": "High",
                "title": "GIS Map Polygon Missing",
                "expected": f"Registered CAD GIS polygon boundary for Survey '{survey_number}'",
                "found": f"No GeoJSON polygon found for Survey '{survey_number}'",
                "description": f"Survey parcel '{survey_number}' does not have a mapped Cadastral spatial polygon in the OpenStreetMap GIS database."
            })
            return {
                "spatial_match": False,
                "parcel_found": False,
                "anomalies": anomalies
            }

        props = parcel_feature.get("properties", {})
        gis_village = props.get("village", "")
        gis_mandal = props.get("mandal", "")
        gis_district = props.get("district", "")

        # 2. Location Mismatch Check
        if doc_village and gis_village and doc_village.lower() != gis_village.lower():
            anomalies.append({
                "type": "SPATIAL_LOCATION_MISMATCH",
                "severity": "High",
                "title": "Village Spatial Boundary Mismatch",
                "expected": f"GIS Boundary Village: '{gis_village}'",
                "found": f"Document Claimed Village: '{doc_village}'",
                "description": f"Document claims parcel location in Village '{doc_village}', but GIS boundary coordinates place Survey {survey_number} in Village '{gis_village}'."
            })

        if doc_district and gis_district and doc_district.lower() != gis_district.lower():
            anomalies.append({
                "type": "SPATIAL_LOCATION_MISMATCH",
                "severity": "High",
                "title": "District Jurisdiction Mismatch",
                "expected": f"GIS Parcel District: '{gis_district}'",
                "found": f"Document Claimed District: '{doc_district}'",
                "description": f"Document claims District '{doc_district}', which differs from official GIS boundary District '{gis_district}'."
            })

        spatial_match = len(anomalies) == 0

        return {
            "spatial_match": spatial_match,
            "parcel_found": True,
            "survey_number": survey_number,
            "gis_properties": props,
            "geometry": parcel_feature.get("geometry"),
            "anomalies": anomalies
        }


# Singleton export
gis_spatial_engine = GISSpatialEngine()
