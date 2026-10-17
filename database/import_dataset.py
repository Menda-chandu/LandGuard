"""Import a LandGuard dataset ZIP into the configured SQLAlchemy database.

Existing upload, verification, and risk rows are preserved. Registry rows are
updated by primary key, so importing the same archive twice is safe.
"""
import argparse
import csv
from datetime import date
import io
import json
from pathlib import Path
import sys
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.database import Base, SessionLocal, engine
from app.models import LandRecord, OwnershipHistory

CSV_MODELS = {
    "land_records.csv": LandRecord,
    "synthetic_land_records_100.csv": LandRecord,
    "ownership_history.csv": OwnershipHistory,
    "synthetic_ownership_history_100.csv": OwnershipHistory,
}
ASSET_NAMES = {
    *CSV_MODELS, "parcels.geojson", "parcels_synthetic_100.geojson",
    "LandGuard_Synthetic_Test_Land_Record.pdf", "ocr_test_synthetic_deed.png",
    "ocr_test_synthetic_deed.jpg", "sample_deed.png", "test_synth_deed.png", "README.md",
}


def import_dataset(archive_path, db, assets_dir):
    objects = []
    assets = {}
    seen = set()
    with zipfile.ZipFile(archive_path) as archive:
        for name in ASSET_NAMES:
            member = f"sample_data/{name}"
            if member in archive.namelist():
                if archive.getinfo(member).file_size > 25 * 1024 * 1024:
                    raise ValueError(f"Dataset file is too large: {name}")
                assets[name] = archive.read(member)
        for name, model in CSV_MODELS.items():
            if name not in assets:
                raise ValueError(f"Required dataset file is missing: {name}")
            rows = csv.DictReader(io.StringIO(assets[name].decode("utf-8-sig")))
            columns = {column.name for column in model.__table__.columns if column.name != "created_at"}
            if not columns.issubset(set(rows.fieldnames or [])):
                raise ValueError(f"Missing CSV columns in {name}")
            key = "record_id" if model is LandRecord else "history_id"
            for row in rows:
                values = {k: (row[k].strip() or None) for k in columns}
                identity = (model.__tablename__, values[key])
                if not values[key] or identity in seen:
                    raise ValueError(f"Missing or duplicate primary key in {name}: {values[key]}")
                seen.add(identity)
                for field in ("registration_date", "transfer_date"):
                    if values.get(field):
                        values[field] = date.fromisoformat(values[field])
                if "land_area_acres" in values:
                    values["land_area_acres"] = float(values["land_area_acres"] or 0)
                objects.append(model(**values))
        for name in ("parcels.geojson", "parcels_synthetic_100.geojson"):
            if name not in assets:
                raise ValueError(f"Required dataset file is missing: {name}")
            data = json.loads(assets[name])
            if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
                raise ValueError(f"Invalid GeoJSON dataset: {name}")
    try:
        for obj in objects:
            db.merge(obj)
        db.commit()
    except Exception:
        db.rollback()
        raise
    assets_dir = Path(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)
    # Copy only explicitly allowed data assets; never extract archive paths or
    # execute the scripts included in the downloaded package.
    for name, content in assets.items():
        (assets_dir / name).write_bytes(content)
    return {"land_records": db.query(LandRecord).count(),
            "ownership_history": db.query(OwnershipHistory).count(), "asset_files": len(assets)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--assets-dir", type=Path, default=PROJECT_ROOT / "sample_data")
    args = parser.parse_args()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        print(json.dumps(import_dataset(args.archive, db, args.assets_dir), indent=2))
