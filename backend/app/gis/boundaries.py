"""Validate WGS84 polygons and compare boundaries in a local metric projection."""
import math
import re
from shapely.geometry import shape, mapping
from shapely import transform
from shapely.errors import GEOSException
from pyproj import CRS, Transformer

ACRE_SQM = 4046.8564224


def validate_geometry(value):
    if not isinstance(value, dict):
        raise ValueError("Provide a GeoJSON Polygon, MultiPolygon, or Feature.")
    geometry = value.get("geometry") if value.get("type") == "Feature" else value
    if not isinstance(geometry, dict) or geometry.get("type") not in ("Polygon", "MultiPolygon"):
        raise ValueError("Boundary must be a Polygon or MultiPolygon in longitude/latitude (WGS84).")
    try:
        polygon = shape(geometry)
    except (GEOSException, ValueError, TypeError, KeyError, IndexError) as error:
        raise ValueError("Boundary coordinates do not form a valid polygon.") from error
    rings = []
    for part in (polygon.geoms if polygon.geom_type == "MultiPolygon" else [polygon]):
        rings.extend([part.exterior, *part.interiors])
    points = [point for ring in rings for point in ring.coords]
    if not points or len(points) > 5000:
        raise ValueError("Boundary must contain between 4 and 5000 vertices.")
    if any(len(p) != 2 or not all(math.isfinite(v) for v in p) or not (-180 <= p[0] <= 180 and -90 < p[1] < 90) for p in points):
        raise ValueError("Use finite [longitude, latitude] pairs within WGS84 bounds.")
    if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
        raise ValueError("Boundary is empty, degenerate, or self-intersecting.")
    if polygon.bounds[2] - polygon.bounds[0] > 1 or polygon.bounds[3] - polygon.bounds[1] > 1:
        raise ValueError("Parcel boundary must span less than one degree.")
    return mapping(polygon)


def compare_boundaries(claimed, registered, parcels, survey_number):
    claimed = validate_geometry(claimed)
    registered = validate_geometry(registered)
    reference = shape(registered)
    center = reference.centroid
    local = CRS.from_proj4(f"+proj=aeqd +lat_0={center.y} +lon_0={center.x} +datum=WGS84 +units=m")
    project = Transformer.from_crs("EPSG:4326", local, always_xy=True).transform
    actual, expected = transform(shape(claimed), project, interleaved=False), transform(reference, project, interleaved=False)
    outside = actual.difference(expected)
    missing = expected.difference(actual)
    union_area = actual.union(expected).area
    difference_ratio = actual.symmetric_difference(expected).area / union_area
    overlaps = []
    skipped_references = []
    for feature in parcels:
        other_survey = feature.get("properties", {}).get("survey_number")
        if not other_survey or other_survey == survey_number:
            continue
        try:
            other = transform(shape(validate_geometry(feature.get("geometry"))), project, interleaved=False)
        except ValueError:
            skipped_references.append(other_survey)
            continue
        # Count only encroachment outside the reference parcel. Existing
        # reference overlaps are not evidence against the uploaded claim.
        overlap = outside.intersection(other).area
        if overlap > max(1.0, actual.area * 0.01):
            overlaps.append({"survey_number": other_survey, "overlap_acres": round(overlap / ACRE_SQM, 6)})
    return {
        "status": "MATCH" if difference_ratio <= 0.02 else "MISMATCH",
        "boundary_match": difference_ratio <= 0.02,
        "tolerance_percent": 2,
        "difference_percent": round(difference_ratio * 100, 3),
        "claimed_area_acres": round(actual.area / ACRE_SQM, 6),
        "registered_geometry_area_acres": round(expected.area / ACRE_SQM, 6),
        "outside_area_acres": round(outside.area / ACRE_SQM, 6),
        "missing_area_acres": round(missing.area / ACRE_SQM, 6),
        "overlapping_parcels": overlaps,
        "unchecked_reference_parcels": skipped_references,
        "claimed_geometry": claimed,
        "reference_geometry": registered,
        "area_source": "Projected GeoJSON geometry; synthetic shapes may differ from registry acreage.",
    }


def compare_boundary_descriptions(claimed, reference):
    normalize = lambda v: re.sub(r"\W+", "", (v or "").casefold())
    result = {}
    for direction in ("north", "south", "east", "west"):
        found, expected = (claimed or {}).get(direction), (reference or {}).get(direction)
        if not found or found == "Not Specified":
            status = "NOT_PROVIDED"
        elif not expected:
            status = "REFERENCE_UNAVAILABLE"
        else:
            status = "MATCH" if normalize(found) == normalize(expected) else "MISMATCH"
        result[direction] = {"status": status, "expected": expected, "found": found}
    return result
