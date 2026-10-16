"""
LandGuard Document Classification Engine.
Analyzes extracted text structure, headers, keywords, and density to classify
the land record into standard legal categories before applying tailored extraction rules.
"""

import re
from typing import Dict, Any, List, Tuple


class DocumentClassifier:
    """
    Classifies land-related documents into standard functional types:
    - Sale Deed
    - Encumbrance Certificate (EC)
    - Patta Passbook / RoR / 7/12 Extract
    - Inheritance / Mutation Record
    - Mortgage Deed / Gift Deed / Partition Deed
    - Survey / Settlement Record
    """

    def __init__(self):
        # Weighted category keyword signatures
        self.signatures = {
            "Sale Deed": [
                (r"\bSALE\s+DEED\b", 40),
                (r"\bCONVEYANCE\s+DEED\b", 35),
                (r"\bDEED\s+OF\s+SALE\b", 40),
                (r"\bVENDOR\b|\bVENDEE\b", 20),
                (r"\bPURCHASER\b|\bBUYER\b", 15),
                (r"\bCONSIDERATION\s+AMOUNT\b", 20),
                (r"\bABSOLUTE\s+OWNER\b", 15),
                (r"\bSALE[\s\-]RECORD\b", 30),
            ],
            "Encumbrance Certificate": [
                (r"\bENCUMBRANCE\s+CERTIFICATE\b", 50),
                (r"\bFORM\s*(?:NO\.?)?\s*15\b|\bFORM\s*(?:NO\.?)?\s*16\b", 40),
                (r"\bNIL\s+ENCUMBRANCE\b", 40),
                (r"\bSTATEMENT\s+OF\s+ENCUMBRANCE\b", 45),
                (r"\bSEARCH\s+PERIOD\b", 25),
                (r"\bNIL\s+TRANSACTIONS?\b", 30),
                (r"\bCERTIFICATE\s+OF\s+ENCUMBRANCE\b", 50),
            ],
            "Patta Passbook / RoR": [
                (r"\bPATTA\s+PASSBOOK\b", 50),
                (r"\bPATTADAR\b", 40),
                (r"\bRECORD\s+OF\s+RIGHTS\b|\bROR\b", 45),
                (r"\b7\s*[\/\-]\s*12\s+EXTRACT\b", 50),
                (r"\bKHATA\s*(?:NO\.?|NUMBER)?\b", 30),
                (r"\bREVENUE\s+DIVISION\b", 20),
                (r"\bRYOTWARI\s+PATTA\b", 40),
            ],
            "Inheritance / Mutation": [
                (r"\bMUTATION\s+PROCEEDINGS?\b", 45),
                (r"\bINHERITANCE\s+MUTATION\b", 50),
                (r"\bLEGAL\s+HEIR\b", 35),
                (r"\bSUCCESSION\s+CERTIFICATE\b", 40),
                (r"\bPARTITION\s+DEED\b", 45),
                (r"\bFAMILY\s+SETTLEMENT\b", 35),
            ],
            "Mortgage Deed": [
                (r"\bMORTGAGE\s+DEED\b", 50),
                (r"\bDEED\s+OF\s+MORTGAGE\b", 50),
                (r"\bMORTGAGOR\b|\bMORTGAGEE\b", 35),
                (r"\bSECURED\s+LOAN\b", 20),
                (r"\bHYPOTHECATION\b", 25),
            ],
            "Gift Deed": [
                (r"\bGIFT\s+DEED\b", 50),
                (r"\bDEED\s+OF\s+GIFT\b", 50),
                (r"\bDONOR\b|\bDONEE\b", 35),
                (r"\bOUT\s+OF\s+NATURAL\s+LOVE\s+AND\s+AFFECTION\b", 40),
            ],
            "Survey Settlement Record": [
                (r"\bSURVEY\s+SETTLEMENT\b", 45),
                (r"\bCADASTRAL\s+MAP\b|\bFMB\s+SKETCH\b", 45),
                (r"\bTIPPON\b|\bFIELD\s+MEASUREMENT\s+BOOK\b", 40),
                (r"\bSUB[\s\-]DIVISION\s+RECORD\b", 35),
            ]
        }

    def classify_document(self, text: str) -> Dict[str, Any]:
        """
        Calculates match scores across document categories.
        Returns the top predicted category, confidence score, and candidate scores.
        """
        if not text or not text.strip():
            return {
                "document_type": "Unknown Document",
                "classification_confidence": 0.0,
                "candidate_scores": {},
                "is_confident": False
            }

        scores = {}
        for category, patterns in self.signatures.items():
            cat_score = 0
            for pat, weight in patterns:
                matches = len(re.findall(pat, text, re.IGNORECASE))
                if matches > 0:
                    cat_score += weight * min(matches, 3)
            scores[category] = cat_score

        top_category = max(scores, key=scores.get)
        top_score = scores[top_category]

        if top_score >= 35:
            # Scale score to a 60% - 98% confidence
            confidence = min(98.0, 60.0 + (top_score * 0.4))
            return {
                "document_type": top_category,
                "classification_confidence": round(confidence, 2),
                "candidate_scores": scores,
                "is_confident": True
            }
        else:
            # If generic land keywords exist
            if re.search(r"\b(?:LAND|SURVEY|PLOT|DEED|REVENUE|RECORD)\b", text, re.IGNORECASE):
                return {
                    "document_type": "General Land Record",
                    "classification_confidence": 55.0,
                    "candidate_scores": scores,
                    "is_confident": False
                }
            return {
                "document_type": "Unclassified Document",
                "classification_confidence": 30.0,
                "candidate_scores": scores,
                "is_confident": False
            }


# Singleton export
document_classifier = DocumentClassifier()


def classify_document_type(text: str) -> Dict[str, Any]:
    """Helper functional wrapper for DocumentClassifier."""
    return document_classifier.classify_document(text)
