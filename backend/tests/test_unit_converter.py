import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.nlp.unit_converter import (
    convert_to_acres,
    convert_to_sqm,
    normalize_land_area,
    compare_areas,
    parse_area_value_and_unit
)


def test_square_yards_to_acres():
    # 240 square yards MUST NOT be 240 acres!
    acres = convert_to_acres(240, "square yards")
    expected = 240.0 / 4840.0
    assert abs(acres - expected) < 1e-6
    assert acres < 0.05
    assert acres != 240.0

    # 4840 square yards == 1 Acre
    assert abs(convert_to_acres(4840, "sq yds") - 1.0) < 1e-6


def test_guntas_to_acres():
    # 40 guntas == 1 Acre
    assert abs(convert_to_acres(40, "guntas") - 1.0) < 1e-6
    # 10 guntas == 0.25 Acres
    assert abs(convert_to_acres(10, "Guntas") - 0.25) < 1e-6


def test_cents_to_acres():
    # 100 cents == 1 Acre
    assert abs(convert_to_acres(100, "cents") - 1.0) < 1e-6
    # 50 cents == 0.5 Acres
    assert abs(convert_to_acres(50, "Cents") - 0.5) < 1e-6


def test_hectares_to_acres():
    # 1 hectare = 2.47105... acres
    acres = convert_to_acres(1.0, "hectares")
    assert abs(acres - 2.47105381) < 1e-4


def test_square_feet_to_acres():
    # 43560 sq ft == 1 Acre
    assert abs(convert_to_acres(43560, "sq ft") - 1.0) < 1e-6


def test_parse_area_value_and_unit():
    val, unit_raw, unit_key = parse_area_value_and_unit("240 square yards")
    assert val == 240.0
    assert unit_raw == "square yards"
    assert unit_key == "square yards"

    val2, unit_raw2, unit_key2 = parse_area_value_and_unit("1,250.75 Sq. Yds")
    assert val2 == 1250.75
    assert "yds" in unit_key2


def test_normalize_land_area():
    norm = normalize_land_area(240, "square yards")
    assert norm["raw_value"] == 240
    assert norm["raw_unit"] == "square yards"
    assert norm["normalized_acres"] == 0.0496
    assert norm["normalized_sqm"] == round(0.0495867 * 4046.8564, 2)
    assert norm["is_reliable"] is True


def test_compare_areas_cross_units():
    # 4840 sq yards vs 1.0 Acre -> should MATCH within tolerance
    res = compare_areas(4840, "sq yds", 1.0, "Acres", tolerance_pct=1.0)
    assert res["match"] is True
    assert res["discrepancy_pct"] < 0.1

    # 240 sq yards vs 2.45 Acres -> massive mismatch
    res2 = compare_areas(240, "square yards", 2.45, "Acres", tolerance_pct=5.0)
    assert res2["match"] is False
    assert res2["discrepancy_pct"] > 90.0
