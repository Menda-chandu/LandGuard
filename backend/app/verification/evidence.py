"""Registration, uploaded-document duplication, and boundary evidence checks."""
import re
from datetime import datetime, date
from sqlalchemy import or_
from app.models import DocumentRecord
from app.gis.boundaries import compare_boundaries, compare_boundary_descriptions
from app.gis.spatial_engine import gis_spatial_engine


def parse_date(value):
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d-%b-%Y", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(value or "", fmt).date()
        except ValueError:
            continue
    return None


def evaluate_evidence(record, fields, doc, db):
    anomalies = []
    checks = {}
    normalize = lambda value: re.sub(r"\W+", "", (value or "").casefold())
    for field in ("registration_number", "registration_date"):
        found = (fields or {}).get(field)
        expected = getattr(record, field)
        status = "NOT_PROVIDED" if not found else "REFERENCE_UNAVAILABLE" if not expected else "MATCH"
        if found and expected:
            actual = parse_date(found) if field.endswith("date") else normalize(found)
            baseline = expected if field.endswith("date") else normalize(expected)
            status = "UNREADABLE" if actual is None else "MATCH" if actual == baseline else "MISMATCH"
        checks[field] = {"status": status, "expected": str(expected) if expected else None, "found": found}
        if status in ("MISMATCH", "UNREADABLE"):
            anomalies.append({"type": field.upper() + "_MISMATCH", "severity": "High",
                              "title": field.replace("_", " ").title() + " Mismatch",
                              "expected": str(expected), "found": found,
                              "description": f"Uploaded {field.replace('_', ' ')} does not match reference record {record.record_id}."})

    duplicate_matches = []
    if doc is not None:
        criteria = []
        if doc.content_sha256:
            criteria.append(DocumentRecord.content_sha256 == doc.content_sha256)
        if doc.text_sha256:
            criteria.append(DocumentRecord.text_sha256 == doc.text_sha256)
        if criteria:
            others = db.query(DocumentRecord).filter(DocumentRecord.document_id != doc.document_id, or_(*criteria)).all()
            duplicate_matches = [{"document_id": other.document_id,
                                  "evidence": "IDENTICAL_FILE" if doc.content_sha256 and other.content_sha256 == doc.content_sha256 else "IDENTICAL_NORMALIZED_TEXT"}
                                 for other in others]
    checks["duplicate_document"] = {"status": "DUPLICATE" if duplicate_matches else "CLEAR" if doc is not None and (doc.content_sha256 or doc.text_sha256) else "NOT_CHECKED", "matches": duplicate_matches}
    if duplicate_matches:
        anomalies.append({"type": "DUPLICATE_DOCUMENT", "severity": "Medium", "title": "Previously Uploaded Document",
                          "expected": "Distinct uploaded document", "found": ", ".join(m["document_id"] for m in duplicate_matches),
                          "description": "File bytes or normalized OCR text match previous uploads. A repeat upload requires review and does not establish fraud."})

    parcel = gis_spatial_engine.get_parcel_by_survey(record.survey_number)
    descriptions = compare_boundary_descriptions((fields or {}).get("boundary_details"), (parcel or {}).get("properties", {}).get("boundary_details"))
    checks["boundary_descriptions"] = descriptions
    for direction, check in descriptions.items():
        if check["status"] == "MISMATCH":
            anomalies.append({"type": "BOUNDARY_DESCRIPTION_MISMATCH", "severity": "High", "title": f"{direction.title()} Boundary Mismatch",
                              "expected": check["expected"], "found": check["found"],
                              "description": f"The {direction} boundary differs from the reference parcel description."})
    checks["boundary_geometry"] = {"status": "NOT_PROVIDED", "boundary_match": None}
    if doc is not None and doc.claimed_geometry:
        import json
        if not parcel:
            checks["boundary_geometry"] = {"status": "REFERENCE_UNAVAILABLE", "boundary_match": None}
        else:
            result = compare_boundaries(json.loads(doc.claimed_geometry), parcel["geometry"], gis_spatial_engine.geojson_data["features"], record.survey_number)
            checks["boundary_geometry"] = result
            if not result["boundary_match"]:
                anomalies.append({"type": "BOUNDARY_GEOMETRY_MISMATCH", "severity": "High", "title": "Parcel Boundary Geometry Mismatch",
                                  "expected": "Claimed polygon within 2% of reference boundary",
                                  "found": f"{result['difference_percent']}% difference; {result['outside_area_acres']} acres outside",
                                  "description": "Projected polygon comparison detects missing land or land outside the registered boundary."})
            if result["overlapping_parcels"]:
                anomalies.append({"type": "PARCEL_ENCROACHMENT", "severity": "High", "title": "Claim Overlaps Another Parcel",
                                  "expected": "No claimed land outside the reference parcel overlaps other mapped parcels",
                                  "found": ", ".join(o["survey_number"] for o in result["overlapping_parcels"]),
                                  "description": "Geometric intersection found claimed land extending into other reference parcels."})
    return checks, anomalies
