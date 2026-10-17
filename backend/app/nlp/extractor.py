import re
import logging

logger = logging.getLogger("landguard.nlp")


class NLPInformationExtractor:
    """
    Rule-based NLP Information Extraction Engine for Land Documents.
    Parses OCR text to extract key deed attributes: owner, survey no, area,
    location hierarchy, registration details, and land parcel boundaries.
    """

    def __init__(self):
        # 1. Document Type Patterns
        self.doc_type_patterns = [
            (r"\b(?:PAHANI|ADANGAL)\b|పహాణి|అడంగల్", "Pahani / Adangal"),
            (r"\bSALE\s+DEED\b", "Sale Deed"),
            (r"\bGIFT\s+DEED\b", "Gift Deed"),
            (r"\bPARTITION\s+DEED\b", "Partition Deed"),
            (r"\bPATTA\s+PASSBOOK\b", "Patta Passbook"),
            (r"\bINHERITANCE\s+MUTATION\b", "Inheritance Mutation"),
            (r"\bTITLE\s+DEED\b", "Title Deed"),
            (r"\bMORTGAGE\s+DEED\b", "Mortgage Deed"),
            (r"\bSALE[\s\-]RECORD\b", "Sale Deed"),
        ]

        # 2. Key Attribute Regex Rules
        self.rules = {
            "owner_name": [
                r"(?:OWNER\s+NAME|NAME\s+OF\s+OWNER)\s*[\:\-\.]*\s*(?:\n\s*)?([A-Za-z\s\.\']{2,40}?)(?=\s*\(|\n|\,|\s+CLAIMED|\s+SURVEY|$)",
                r"(?:[\(\[])?\s*(?:EXECUTANT\s*(?:\/\s*OWNER\s*NAME)?|SELLER|OWNER|CLAIMED\s+OWNER|TITLE\s+HOLDER)\s*(?:[\(\[][^\)\n\!]*[\)\]\!])?\s*[\:\-\.]?\s+([A-Za-z\s\.\']{3,40}?)(?=\n|\,|\s+CLAIMED|\s+SURVEY|\s+VILLAGE|\s+SON|\s+WIFE|\s+DAUGHTER|$)",
                r"(?:IN FAVOUR OF|PROPERTIES OF)\s*[\:\-\.]?\s*([A-Za-z\s\.\']{3,40}?)(?=\n|\,|\s+CLAIMED|\s+SURVEY|$)",
            ],
            "survey_number": [
                r"(?:CLAIMED\s+SURVEY[A-Z]*|SURVEY\s*(?:NO\.?|NUMBER)?|SY\s*NO\.?|PLOT\s*NO\.?)\s*[\:\-\.]*\s*(?:\n\s*)?([A-Za-z0-9\-]+\/[0-9A-Za-z]+|[0-9]{1,4}\/[0-9A-Z]+|[0-9]{1,4})",
                r"(?:SURVEY|PLOT)\s*[\:\-\.]*\s*(?:\n\s*)?([A-Za-z0-9\-]+\/[0-9A-Za-z]+|[0-9]{1,4}\/[0-9A-Z]+|[0-9]{1,4})"
            ],
            "land_area": [
                r"(?:CLAIMED\s+EXTENT|LAND\s+AREA|TOTAL\s+AREA|EXTENT)[ \t]*[\:\-\.]*[ \t]*(?:\n[ \t]*)?([0-9]+(?:\.[0-9]+)?)[ \t]*([A-Za-z. \t]+)?(?=\n|$)",
                r"([0-9]+(?:\.[0-9]+)?)\s*(ACRES|ACRE|AC|SQUARE\s+YARDS|SQ\s+YARDS|SQ\.\s+YARDS|SQ\s+YDS|HECTARES|HA|GUNTAS)"
            ],
            "village": [
                r"(?:VILLAGE\s*(?:\/\s*LOCALITY)?|LOCALITY)\s*[\:\-\.]*\s*(?:\n\s*)?([A-Za-z0-9\s]{2,40}?)(?=\s*\(|\,|\s+MANDAL|\s+DISTRICT|\n|$)",
                r"VILLAGE\s+([A-Za-z\s]{3,30}?)(?=\,|\s+MANDAL|\s+DISTRICT|\n|$)"
            ],
            "mandal": [
                r"(?:MANDAL|TALUK)\s*[\:\-\.]*\s*(?:\n\s*)?([A-Za-z0-9\s]{2,40}?)(?=\s*\(|\,|\s+DISTRICT|\n|$)",
                r"MANDAL\s+([A-Za-z\s]{3,30}?)(?=\,|\s+DISTRICT|\n|$)"
            ],
            "district": [
                r"(?:DISTRICT|DISTROCT|DIST)\s*[\:\-\.]*\s*(?:\n\s*)?([A-Za-z0-9\s]{2,40}?)(?=\s*\(|\,|\s+STATE|\n|$)",
                r"([A-Za-z\s]{3,30}?)\s+DISTRICT(?!\s+OFFICE)"
            ],
            "state": [
                r"(?:STATE)\s*[\:\-\.]*\s*(?:\n\s*)?([A-Za-z0-9\s]{2,40}?)(?=\s*\(|\,|\n|$)"
            ],
            "registration_number": [
                r"(?:DOCUMENT\s*(?:NUMBER|NO\.?|ID|IO)|REGISTRATION\s+NO|REG\s+NO|DEED\s+NO)\s*[\:\-\.]*\s*(?:\n\s*)?([A-Z0-9\-\/]{4,40})"
            ],
            "registration_date": [
                r"(?:DOCUMENT\s+DATE|REGISTRATION\s+DATE|EXECUTION\s+DATE|DATE)\s*[\:\-\.]*\s*(?:\n\s*)?([0-9]{1,2}\s+[A-Za-z]{3,10}\s+[0-9]{4}|[0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}|[0-9]{1,2}\-[A-Za-z]{3}\-[0-9]{4}|[0-9]{4}\-[0-9]{2}\-[0-9]{2})"
            ]
        }

        # 3. Boundary Regex Patterns
        self.boundary_patterns = {
            "north": r"(?:BOUNDARY\s*[\:\-]?\s*NORTH|NORTH(?:ERN\s+BOUNDARY)?)\s*[\:\-]*\s*(?:\n\s*)?([^\n\.\;]+)",
            "south": r"(?:BOUNDARY\s*[\:\-]?\s*SOUTH|SOUTH(?:ERN\s+BOUNDARY)?)\s*[\:\-]*\s*(?:\n\s*)?([^\n\.\;]+)",
            "east": r"(?:BOUNDARY\s*[\:\-]?\s*EAST|EAST(?:ERN\s+BOUNDARY)?)\s*[\:\-]*\s*(?:\n\s*)?([^\n\.\;]+)",
            "west": r"(?:BOUNDARY\s*[\:\-]?\s*WEST|WEST(?:ERN\s+BOUNDARY)?)\s*[\:\-]*\s*(?:\n\s*)?([^\n\.\;]+)"
        }

        # Labelled English and Telugu Pahani/Adangal records. These aliases
        # preserve Unicode names; unlabelled multi-row tables require review.
        aliases = {
            "owner_name": r"PATTADAR(?:\s+NAME)?|PATTADHAR(?:\s+NAME)?|పట్టాదారు\s*పేరు|పట్టాదారు",
            "survey_number": r"SURVEY\s*(?:NO\.?|NUMBER)|సర్వే\s*(?:నంబరు|నెంబర్|సంఖ్య)",
            "village": r"REVENUE\s+VILLAGE|గ్రామం",
            "mandal": r"మండలం", "district": r"జిల్లా",
        }
        for field, labels in aliases.items():
            self.rules[field].insert(0, rf"(?:{labels})[ \t]*[:\-][ \t]*([^\n]+)")
        self.rules["land_area"].insert(0, r"(?:విస్తీర్ణం|EXTENT\s*\(ACRES\))[ \t]*[:\-][ \t]*([0-9]+(?:\.[0-9]+)?)[ \t]*([^\n]*)")
        self.rules["khata_number"] = [r"(?:KHATA\s*(?:NO\.?|NUMBER)|ఖాతా\s*నంబరు)[ \t]*[:\-][ \t]*([A-Za-z0-9/\-]+)"]
        self.rules["crop_year"] = [r"(?:CROP\s+YEAR|AGRICULTURAL\s+YEAR|పంట\s*సంవత్సరం)[ \t]*[:\-][ \t]*([0-9]{4}(?:[\-/][0-9]{2,4})?)"]

    def extract_information(self, ocr_text: str) -> dict:
        """
        Extracts structured fields from raw OCR text using regex rule engine.
        Returns a dictionary with extracted attributes, boundaries, and field extraction confidence.
        """
        if not ocr_text or not ocr_text.strip():
            return self._empty_extraction_payload("No OCR text provided for extraction")

        clean_text = self._clean_ocr_text(ocr_text)

        # 1. Document Type Extraction
        extracted_doc_type = "Unknown"
        # A labelled document/record type takes precedence over incidental text
        # such as a disclaimer saying that this is not an official title deed.
        type_label = re.search(
            r"(?:DEED TITLE|DOCUMENT TYPE|RECORD TYPE|INSTRUMENT)[ \t]*[:\-]?[ \t]*\n?[ \t]*([^\n]+)",
            clean_text, re.IGNORECASE,
        )
        type_text = type_label.group(1) if type_label else clean_text
        for pattern, label in self.doc_type_patterns:
            if re.search(pattern, type_text, re.IGNORECASE):
                extracted_doc_type = label
                break

        # 2. Extract Primary Fields
        extracted_data = {
            "document_type": extracted_doc_type,
            "owner_name": None,
            "survey_number": None,
            "land_area_acres": None,
            "land_area_raw": None,
            "land_area_unit": None,
            "village": None,
            "mandal": None,
            "district": None,
            "state": None,
            "registration_number": None,
            "registration_date": None,
            "khata_number": None,
            "crop_year": None,
        }

        fields_found_count = 0

        for field_name, pattern_list in self.rules.items():
            for pattern in pattern_list:
                match = re.search(pattern, clean_text, re.IGNORECASE)
                if match:
                    if field_name == "land_area":
                        num_str = match.group(1).strip()
                        raw_unit = (match.group(2) if len(match.groups()) > 1 and match.group(2) else "Acres").strip()
                        raw_unit_clean = re.sub(r"[,\.]+$", "", raw_unit).strip() or "Acres"
                        try:
                            num_val = float(num_str)
                            unit = re.sub(r"[^a-z]", "", raw_unit_clean.lower())
                            factors = {
                                "acres": 1, "acre": 1, "ac": 1,
                                "squareyards": 1 / 4840, "sqyards": 1 / 4840, "sqyds": 1 / 4840,
                                "squarefeet": 1 / 43560, "sqfeet": 1 / 43560, "sqft": 1 / 43560,
                                "hectares": 2.4710538147, "hectare": 2.4710538147, "ha": 2.4710538147,
                                "guntas": 0.025, "gunta": 0.025,
                                "squaremeters": 1 / 4046.8564224, "squaremetres": 1 / 4046.8564224,
                                "sqm": 1 / 4046.8564224,
                            }
                            extracted_data["land_area_acres"] = round(num_val * factors[unit], 6) if unit in factors else None
                            extracted_data["land_area_raw"] = f"{num_str} {raw_unit_clean}"
                            extracted_data["land_area_unit"] = raw_unit_clean
                            fields_found_count += 1
                        except ValueError:
                            continue
                        break
                    else:
                        val = match.group(1).strip()
                        # Clean up parentheticals
                        val = re.sub(r"\(.*?\)", "", val).strip()

                        if field_name == "owner_name":
                            val = re.sub(r"\s+", " ", val).title()
                        elif field_name == "survey_number":
                            val = val.upper()
                        elif field_name in ["village", "mandal", "district", "state"]:
                            val = val.strip(",. ").title()

                        extracted_data[field_name] = val
                        fields_found_count += 1
                        break

        # 3. Extract Parcel Boundary Details (North, South, East, West)
        boundaries = {}
        for direction, b_pattern in self.boundary_patterns.items():
            b_match = re.search(b_pattern, clean_text, re.IGNORECASE)
            if b_match:
                b_val = b_match.group(1).strip()
                b_val = re.sub(r"\(.*?\)", "", b_val).strip()
                boundaries[direction] = b_val
            else:
                boundaries[direction] = "Not Specified"

        extracted_data["boundary_details"] = boundaries

        # 4. Calculate Extraction Confidence Score
        total_fields_tracked = len(self.rules)
        confidence_score = round((fields_found_count / total_fields_tracked) * 100, 2)

        # Build Location String Summary
        location_parts = [
            extracted_data.get("village"),
            extracted_data.get("mandal"),
            extracted_data.get("district"),
            extracted_data.get("state")
        ]
        location_summary = ", ".join([p for p in location_parts if p]) or "Location Unspecified"

        return {
            "status": "SUCCESS",
            "extracted_fields": extracted_data,
            "location_summary": location_summary,
            "fields_extracted_count": fields_found_count,
            "nlp_confidence_score": confidence_score
        }

    def _clean_ocr_text(self, text: str) -> str:
        """
        Normalize OCR text by fixing common character glitches.
        """
        cleaned = re.sub(r"[\r\t]+", " ", text)
        return cleaned

    def _empty_extraction_payload(self, reason: str) -> dict:
        return {
            "status": "EMPTY",
            "reason": reason,
            "extracted_fields": {
                "document_type": "Unknown",
                "owner_name": None,
                "survey_number": None,
                "land_area_acres": 0.0,
                "land_area_raw": None,
                "land_area_unit": None,
                "village": None,
                "mandal": None,
                "district": None,
                "state": None,
                "registration_number": None,
                "registration_date": None,
                "boundary_details": {
                    "north": "Not Specified",
                    "south": "Not Specified",
                    "east": "Not Specified",
                    "west": "Not Specified"
                }
            },
            "location_summary": "Unspecified",
            "fields_extracted_count": 0,
            "nlp_confidence_score": 0.0
        }


# Singleton instance for export
nlp_engine = NLPInformationExtractor()
