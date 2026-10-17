"""Duplicate evidence: exact file bytes and substantive normalized OCR text."""
import hashlib
import re
import unicodedata


def file_fingerprint(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_fingerprint(text):
    normalized = re.sub(r"\W+", "", unicodedata.normalize("NFKC", text or "").casefold())
    # Empty/error/very short OCR output is never duplicate evidence.
    if len(normalized) < 80 or normalized.startswith(("ocrengineunavailable", "ocrprocessingerror", "blankorlowcontrast")):
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
