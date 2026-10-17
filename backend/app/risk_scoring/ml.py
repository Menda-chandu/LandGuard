"""Exploratory unsupervised anomaly detection on the imported reference data.

Isolation Forest learns the reference feature distribution. Its percentile is
an outlier rank, never a calibrated probability of fraud. No fabricated labels.
"""
from collections import defaultdict, Counter
import math
import numpy as np
from sklearn.ensemble import IsolationForest
from app.models import LandRecord, OwnershipHistory


FEATURE_NAMES = ["log parcel acreage", "same-survey registrations", "ownership history entries", "transfers within 60 days"]


def assess_reference_outlier(db, matched_record, claimed_area=None):
    records = db.query(LandRecord).order_by(LandRecord.record_id).all()
    if not matched_record or len(records) < 20:
        return {"status": "INSUFFICIENT_REFERENCE_DATA", "training_records": len(records), "risk_points": 0}
    histories = defaultdict(list)
    for row in db.query(OwnershipHistory).all():
        if row.transfer_date:
            histories[row.survey_number].append(row.transfer_date)
    counts = Counter(r.survey_number for r in records)

    def features(record, area=None):
        dates = sorted(histories[record.survey_number])
        rapid = max((sum(0 <= (d - first).days <= 60 for d in dates) for first in dates), default=0)
        return [math.log1p(max(0, float(record.land_area_acres) if area is None else float(area))),
                counts[record.survey_number], len(dates), rapid]

    matrix = np.asarray([features(r) for r in records], dtype=float)
    model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42, n_jobs=1).fit(matrix)
    record = next(r for r in records if r.record_id == matched_record["record_id"])
    sample = np.asarray([features(record, claimed_area)], dtype=float)
    training_scores = -model.score_samples(matrix)
    sample_score = float(-model.score_samples(sample)[0])
    percentile = float(np.mean(training_scores < sample_score) * 100)
    flagged = percentile >= 95 and model.predict(sample)[0] == -1
    medians = np.median(matrix, axis=0)
    deviations = abs(sample[0] - medians) / np.maximum(np.std(matrix, axis=0), 0.01)
    ranked = np.argsort(deviations)[::-1]
    reasons = [{"feature": FEATURE_NAMES[i], "document_value": round(float(sample[0][i]), 4),
                "reference_median": round(float(medians[i]), 4)} for i in ranked[:2] if deviations[i] > 1]
    return {"status": "ASSESSED", "model": "IsolationForest", "training_records": len(records),
            "training_source": "Imported reference registry and ownership history (synthetic demo data)",
            "outlier_percentile": round(percentile, 2), "flagged": bool(flagged), "risk_points": 10 if flagged else 0,
            "explanation": reasons, "limitation": "Exploratory outlier rank, not fraud probability. Requires real labelled data for fraud accuracy validation."}
