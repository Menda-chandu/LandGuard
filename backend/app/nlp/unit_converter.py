"""
LandGuard Land Area Unit Converter Module.
Provides verified mathematical conversions between Indian land measurement units:
Acres, Square Yards (Gaj), Guntas, Cents, Hectares, Square Feet, and Square Meters.
"""

import re
from typing import Dict, Any, Optional, Tuple

# Exact mathematical constants relative to 1 Acre
# 1 Acre = 4,840 Square Yards
# 1 Acre = 40 Guntas (in Telangana, Andhra Pradesh, Karnataka, Maharashtra)
# 1 Acre = 100 Cents (in Tamil Nadu, Kerala, Andhra Pradesh)
# 1 Acre = 43,560 Square Feet
# 1 Acre = 4,046.8564224 Square Meters
# 1 Hectare = 2.47105381 Acres = 10,000 Square Meters

ACRE_CONVERSIONS = {
    "acre": 1.0,
    "acres": 1.0,
    "ac": 1.0,
    "square yard": 1.0 / 4840.0,
    "square yards": 1.0 / 4840.0,
    "sq yard": 1.0 / 4840.0,
    "sq yards": 1.0 / 4840.0,
    "sq.yard": 1.0 / 4840.0,
    "sq.yards": 1.0 / 4840.0,
    "sq yds": 1.0 / 4840.0,
    "sq.yds": 1.0 / 4840.0,
    "sq yd": 1.0 / 4840.0,
    "gaj": 1.0 / 4840.0,
    "guntha": 1.0 / 40.0,
    "gunthas": 1.0 / 40.0,
    "gunta": 1.0 / 40.0,
    "guntas": 1.0 / 40.0,
    "cent": 1.0 / 100.0,
    "cents": 1.0 / 100.0,
    "ct": 1.0 / 100.0,
    "hectare": 2.47105381,
    "hectares": 2.47105381,
    "ha": 2.47105381,
    "square foot": 1.0 / 43560.0,
    "square feet": 1.0 / 43560.0,
    "sq foot": 1.0 / 43560.0,
    "sq feet": 1.0 / 43560.0,
    "sq.ft": 1.0 / 43560.0,
    "sq ft": 1.0 / 43560.0,
    "sft": 1.0 / 43560.0,
    "square meter": 1.0 / 4046.8564224,
    "square meters": 1.0 / 4046.8564224,
    "sq meter": 1.0 / 4046.8564224,
    "sq meters": 1.0 / 4046.8564224,
    "sq.m": 1.0 / 4046.8564224,
    "sq m": 1.0 / 4046.8564224,
    "sqm": 1.0 / 4046.8564224
}

SQM_PER_ACRE = 4046.8564224


def clean_unit_string(unit_raw: Optional[str]) -> str:
    """Normalize raw unit string to standard lowercase key."""
    if not unit_raw:
        return "acres"
    clean = re.sub(r"[,\.;:\-\(\)\[\]]+", " ", unit_raw.lower()).strip()
    clean = re.sub(r"\s+", " ", clean)
    return clean or "acres"


def parse_area_value_and_unit(area_str: str) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """
    Parses a string like '240 square yards', '2.45 Acres', or '10 Guntas'.
    Returns (numeric_value, raw_unit, normalized_unit_key).
    """
    if not area_str or not area_str.strip():
        return None, None, None

    # Strip commas inside numbers: e.g. 1,200.50 -> 1200.50
    cleaned = re.sub(r"(?<=\d),(?=\d)", "", area_str.strip())

    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z\s\.]+)?", cleaned)
    if not match:
        return None, None, None

    try:
        val = float(match.group(1))
    except (ValueError, TypeError):
        return None, None, None

    unit_raw = match.group(2).strip() if match.group(2) else "Acres"
    unit_key = clean_unit_string(unit_raw)

    return val, unit_raw, unit_key


def convert_to_acres(value: float, unit_str: str) -> float:
    """
    Converts a land area value with specified unit to Acres.
    Example: 240 square yards -> 240 / 4840 = 0.0495867... Acres.
    """
    unit_key = clean_unit_string(unit_str)
    multiplier = ACRE_CONVERSIONS.get(unit_key)
    if multiplier is None:
        # Fallback partial matching
        for k, v in ACRE_CONVERSIONS.items():
            if k in unit_key or unit_key in k:
                multiplier = v
                break

    if multiplier is None:
        # If unknown unit, assume 1.0 (acres)
        multiplier = 1.0

    return value * multiplier


def convert_to_sqm(acres: float) -> float:
    """Converts area in Acres to Square Meters."""
    return acres * SQM_PER_ACRE


def normalize_land_area(
    value: float,
    unit_str: str,
    raw_str: Optional[str] = None
) -> Dict[str, Any]:
    """
    Normalizes a land area into standard structure:
    - raw_value: original float
    - raw_unit: original unit text
    - raw_text: complete original string
    - normalized_acres: float in acres (rounded to 4 decimal places)
    - normalized_sqm: float in square meters (rounded to 2 decimal places)
    - is_reliable: boolean flag
    """
    normalized_acres = convert_to_acres(value, unit_str)
    normalized_sqm = convert_to_sqm(normalized_acres)

    return {
        "raw_value": value,
        "raw_unit": unit_str,
        "raw_text": raw_str or f"{value} {unit_str}".strip(),
        "normalized_acres": round(normalized_acres, 4),
        "normalized_sqm": round(normalized_sqm, 2),
        "is_reliable": value > 0 and clean_unit_string(unit_str) in ACRE_CONVERSIONS
    }


def compare_areas(
    doc_area: float,
    doc_unit: str,
    ref_area: float,
    ref_unit: str = "Acres",
    tolerance_pct: float = 5.0
) -> Dict[str, Any]:
    """
    Compares two land areas across any units by converting both to Acres.
    Returns comparison result with tolerance check.
    """
    doc_acres = convert_to_acres(doc_area, doc_unit)
    ref_acres = convert_to_acres(ref_area, ref_unit)

    if ref_acres <= 0.0:
        return {
            "match": False,
            "discrepancy_pct": 100.0,
            "doc_acres": round(doc_acres, 4),
            "ref_acres": round(ref_acres, 4),
            "difference_acres": round(abs(doc_acres - ref_acres), 4),
            "note": "Reference area is zero or missing"
        }

    diff_acres = abs(doc_acres - ref_acres)
    pct_diff = (diff_acres / ref_acres) * 100.0
    is_match = pct_diff <= tolerance_pct

    return {
        "match": is_match,
        "discrepancy_pct": round(pct_diff, 2),
        "doc_acres": round(doc_acres, 4),
        "ref_acres": round(ref_acres, 4),
        "difference_acres": round(diff_acres, 4),
        "within_tolerance": is_match,
        "tolerance_pct": tolerance_pct
    }
