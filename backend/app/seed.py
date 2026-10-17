"""Seed only an empty demonstration registry; never overwrite existing records."""
import csv
from datetime import date
from app.models import LandRecord, OwnershipHistory


def seed_demo_registry(db, dataset_dir):
    if db.query(LandRecord).count() or db.query(OwnershipHistory).count():
        return False
    for name, model in (("land_records.csv", LandRecord), ("synthetic_land_records_100.csv", LandRecord),
                        ("ownership_history.csv", OwnershipHistory), ("synthetic_ownership_history_100.csv", OwnershipHistory)):
        with (dataset_dir / name).open(encoding="utf-8-sig", newline="") as source:
            for row in csv.DictReader(source):
                values = {key: value.strip() or None for key, value in row.items()}
                for key in ("registration_date", "transfer_date"):
                    if values.get(key):
                        values[key] = date.fromisoformat(values[key])
                if "land_area_acres" in values:
                    values["land_area_acres"] = float(values["land_area_acres"] or 0)
                db.add(model(**values))
    db.commit()
    return True
