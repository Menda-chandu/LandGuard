import os
import sys
import io
import re
import zlib
import base64
import logging
from typing import Dict, Any, List, Tuple
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None

from app.ocr.preprocessor import enhance_document_image

logger = logging.getLogger("landguard.ocr")


def configure_tesseract_path() -> str | None:
    """
    Auto-detect Tesseract binary path on Windows / Linux systems.
    """
    if not pytesseract:
        return None

    configured_path = os.getenv("TESSERACT_PATH", "").strip()
    try:
        from app.config import settings
        if not configured_path and hasattr(settings, "TESSERACT_PATH"):
            configured_path = settings.TESSERACT_PATH
    except Exception:
        pass

    # Common Windows and Linux Tesseract binary paths
    possible_paths = [
        configured_path,
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]

    for path in possible_paths:
        if path and os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            logger.info(f"Tesseract executable found at: {path}")
            return path

    return None


# Initialize on module load
configure_tesseract_path()


def _is_tesseract_in_path() -> bool:
    if not pytesseract:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _ocr_pil_image(image: Image.Image, apply_enhancement: bool = True) -> Tuple[str, float]:
    """
    Run Tesseract OCR on a PIL Image and calculate word-level confidence score.
    Returns (extracted_text, confidence_score).
    """
    configure_tesseract_path()
    if not pytesseract or not _is_tesseract_in_path():
        return "", 0.0

    processed_img = enhance_document_image(image) if apply_enhancement else image
    try:
        extracted_text = pytesseract.image_to_string(processed_img).strip()
    except Exception as e:
        logger.warning(f"Tesseract image_to_string notice: {e}")
        extracted_text = ""

    confidence = 0.0
    if extracted_text:
        try:
            data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
            conf_values = [int(c) for c in data.get('conf', []) if c != '-1' and str(c).isdigit()]
            if conf_values:
                confidence = round(sum(conf_values) / len(conf_values), 2)
            else:
                confidence = 85.0
        except Exception:
            confidence = 85.0

    return extracted_text, confidence


def extract_text_from_image(image_path: str) -> Dict[str, Any]:
    """
    Extract text and confidence score from an image file (PNG, JPG, TIFF, BMP)
    using enhanced computer-vision preprocessing and Tesseract OCR.
    """
    if not os.path.exists(image_path):
        return {
            "status": "FAILED",
            "text": "",
            "confidence": 0.0,
            "error": "Image file not found",
            "pages_count": 0,
            "pages": []
        }

    configure_tesseract_path()
    if not pytesseract or not _is_tesseract_in_path():
        logger.warning("Tesseract OCR binary not detected on system.")
        return {
            "status": "OCR_ENGINE_UNAVAILABLE",
            "text": "[OCR Engine Unavailable: Tesseract OCR binary not detected on system.]",
            "confidence": 0.0,
            "engine": "Unavailable",
            "error": "Tesseract OCR binary not detected on system.",
            "pages_count": 0,
            "pages": []
        }

    try:
        with Image.open(image_path) as img:
            # Check for empty / corrupt zero-size image
            if img.width <= 10 or img.height <= 10:
                return {
                    "status": "UNREADABLE",
                    "text": "[Unreadable Image: Image dimensions too small or corrupted.]",
                    "confidence": 0.0,
                    "engine": "Document Reader",
                    "error": "Image dimensions too small or corrupted.",
                    "pages_count": 1,
                    "pages": []
                }

            extracted_text, confidence = _ocr_pil_image(img, apply_enhancement=True)

            if not extracted_text:
                return {
                    "status": "WARNING",
                    "text": "[Blank or low-contrast scan. No readable text extracted by OCR engine.]",
                    "confidence": 0.0,
                    "engine": "Tesseract OCR",
                    "pages_count": 1,
                    "pages": [{
                        "page_number": 1,
                        "text": "",
                        "confidence": 0.0,
                        "char_count": 0
                    }]
                }

            page_info = {
                "page_number": 1,
                "text": extracted_text,
                "confidence": confidence,
                "char_count": len(extracted_text)
            }

            return {
                "status": "COMPLETED",
                "text": extracted_text,
                "confidence": confidence,
                "engine": "Tesseract OCR (Enhanced Scan)",
                "pages_count": 1,
                "pages": [page_info]
            }
    except Exception as e:
        logger.error(f"OCR Processing Error on {image_path}: {e}")
        return {
            "status": "FAILED",
            "text": f"[OCR Processing Error: {str(e)}]",
            "confidence": 0.0,
            "engine": "Tesseract OCR",
            "error": str(e),
            "pages_count": 0,
            "pages": []
        }


def _extract_text_pure_python_streams(pdf_path: str) -> str:
    """
    Fallback parser extracting text directly from uncompressed or flate/ascii85 decoded PDF streams
    without external dependencies.
    """
    try:
        with open(pdf_path, 'rb') as f:
            data = f.read()

        text_parts = []
        streams = re.findall(rb'stream[\r\n]+(.*?)[\r\n]*endstream', data, re.DOTALL)
        for s in streams:
            decomp = None
            try:
                decomp = zlib.decompress(s)
            except Exception:
                pass

            if decomp is None:
                try:
                    raw = s.strip()
                    if not raw.endswith(b'~>'):
                        raw = raw + b'~>'
                    a85 = base64.a85decode(raw, adobe=True)
                    decomp = zlib.decompress(a85)
                except Exception:
                    pass

            if decomp is None:
                continue

            decomp_str = decomp.decode('latin1', errors='ignore')

            # Extract literal text strings
            matches = re.findall(r'\(((?:[^()\\]|\\.)*)\)\s*(?:Tj|\'|\"|TJ)', decomp_str)
            arr_matches = re.findall(r'\[(.*?)\]\s*TJ', decomp_str)
            for arr in arr_matches:
                sub = re.findall(r'\(((?:[^()\\]|\\.)*)\)', arr)
                matches.extend(sub)

            for m in matches:
                cleaned = m.replace(r'\(', '(').replace(r'\)', ')').replace(r'\\', '\\')
                cleaned = re.sub(r'\\([0-7]{3})', lambda mo: chr(int(mo.group(1), 8)), cleaned)
                cleaned = cleaned.strip()
                if cleaned:
                    text_parts.append(cleaned)

        return "\n".join(text_parts).strip()
    except Exception as err:
        logger.debug(f"Pure python stream extraction notice: {err}")
        return ""


def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Universal multi-tier extraction engine for PDF documents:
    1. Direct digital text extraction via pypdf with per-page tracking.
    2. Embedded page image extraction via pypdf + Tesseract OCR with quality enhancement.
    3. Raster page rendering via pdf2image + Tesseract OCR (if poppler is available).
    4. Pure-Python stream extraction fallback.
    Never returns fabricated mock deed values.
    """
    if not os.path.exists(pdf_path):
        return {
            "status": "FAILED",
            "text": "",
            "confidence": 0.0,
            "error": "PDF file not found",
            "pages_count": 0,
            "pages": []
        }

    # Check for empty file
    file_size = os.path.getsize(pdf_path)
    if file_size < 32:
        return {
            "status": "UNREADABLE",
            "text": "[Unreadable Document: File is empty or zero bytes.]",
            "confidence": 0.0,
            "engine": "Document Reader",
            "error": "File size too small (empty file).",
            "pages_count": 0,
            "pages": []
        }

    # --- Tier 1: Direct digital text extraction via pypdf ---
    if pypdf:
        try:
            reader = pypdf.PdfReader(pdf_path)
            # Check encryption
            if reader.is_encrypted:
                try:
                    # Attempt empty password decrypt
                    reader.decrypt("")
                except Exception:
                    return {
                        "status": "ENCRYPTED",
                        "text": "[Encrypted Document: PDF file is password protected.]",
                        "confidence": 0.0,
                        "engine": "Document Reader",
                        "error": "PDF file is encrypted or password-protected.",
                        "pages_count": 0,
                        "pages": []
                    }

            extracted_pages = []
            total_chars = 0
            num_pages = len(reader.pages)

            for idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                page_text_clean = page_text.strip()
                extracted_pages.append({
                    "page_number": idx,
                    "text": page_text_clean,
                    "confidence": 95.0 if page_text_clean else 0.0,
                    "char_count": len(page_text_clean)
                })
                total_chars += len(page_text_clean)

            # If meaningful digital text was found across pages
            if total_chars >= 20:
                combined_text_parts = []
                for p in extracted_pages:
                    if p["text"]:
                        if num_pages > 1:
                            combined_text_parts.append(f"--- Page {p['page_number']} ---\n{p['text']}")
                        else:
                            combined_text_parts.append(p["text"])

                full_text = "\n\n".join(combined_text_parts).strip()
                confidence = round(min(98.5, max(89.0, 92.0 + total_chars / 500)), 2)

                return {
                    "status": "COMPLETED",
                    "text": full_text,
                    "confidence": confidence,
                    "engine": "LandGuard Digital PDF Engine",
                    "pages_count": num_pages,
                    "pages": extracted_pages
                }

        except Exception as e:
            logger.info(f"pypdf direct text extraction notice: {e}")

    # --- Tier 2: Extract embedded page images via pypdf and run Tesseract OCR ---
    if pypdf and pytesseract and _is_tesseract_in_path():
        try:
            reader = pypdf.PdfReader(pdf_path)
            num_pages = len(reader.pages)
            image_pages = []
            total_conf = 0.0
            image_count = 0

            for idx, page in enumerate(reader.pages, start=1):
                page_texts = []
                page_confs = []
                for img_file in page.images:
                    try:
                        pil_img = Image.open(io.BytesIO(img_file.data))
                        txt, conf = _ocr_pil_image(pil_img, apply_enhancement=True)
                        if txt:
                            page_texts.append(txt)
                            page_confs.append(conf)
                            total_conf += conf
                            image_count += 1
                    except Exception as img_err:
                        logger.debug(f"Page image OCR notice: {img_err}")

                combined_page_txt = "\n".join(page_texts).strip()
                avg_page_conf = round(sum(page_confs) / max(len(page_confs), 1), 2) if page_confs else 0.0
                image_pages.append({
                    "page_number": idx,
                    "text": combined_page_txt,
                    "confidence": avg_page_conf,
                    "char_count": len(combined_page_txt)
                })

            valid_texts = [p for p in image_pages if p["text"]]
            if valid_texts:
                avg_conf = round(total_conf / max(image_count, 1), 2)
                combined_text_parts = []
                for p in image_pages:
                    if p["text"]:
                        if num_pages > 1:
                            combined_text_parts.append(f"--- Page {p['page_number']} ---\n{p['text']}")
                        else:
                            combined_text_parts.append(p["text"])

                return {
                    "status": "COMPLETED",
                    "text": "\n\n".join(combined_text_parts),
                    "confidence": avg_conf,
                    "engine": "Tesseract OCR (Embedded Image Scan)",
                    "pages_count": num_pages,
                    "pages": image_pages
                }
        except Exception as e:
            logger.info(f"pypdf embedded image extraction notice: {e}")

    # --- Tier 3: Render pages to images via pdf2image (if poppler is installed) ---
    if convert_from_path and pytesseract and _is_tesseract_in_path():
        try:
            images = convert_from_path(pdf_path, first_page=1, last_page=5)
            rendered_pages = []
            total_conf = 0.0

            for idx, img in enumerate(images, start=1):
                txt, conf = _ocr_pil_image(img, apply_enhancement=True)
                total_conf += conf
                rendered_pages.append({
                    "page_number": idx,
                    "text": txt,
                    "confidence": conf,
                    "char_count": len(txt)
                })

            valid_rendered = [p for p in rendered_pages if p["text"]]
            if valid_rendered:
                avg_conf = round(total_conf / max(len(images), 1), 2)
                combined_text_parts = [
                    f"--- Page {p['page_number']} ---\n{p['text']}" if len(images) > 1 else p['text']
                    for p in rendered_pages if p["text"]
                ]
                return {
                    "status": "COMPLETED",
                    "text": "\n\n".join(combined_text_parts),
                    "confidence": avg_conf,
                    "engine": "Tesseract OCR (PDF Render)",
                    "pages_count": len(images),
                    "pages": rendered_pages
                }
        except Exception as e:
            logger.info(f"Poppler PDF conversion notice: {e}")

    # --- Tier 4: Pure Python content-stream parser fallback ---
    stream_text = _extract_text_pure_python_streams(pdf_path)
    if stream_text and len(stream_text) >= 20:
        confidence = round(min(97.0, max(85.0, 88.0 + len(stream_text) / 500)), 2)
        return {
            "status": "COMPLETED",
            "text": stream_text,
            "confidence": confidence,
            "engine": "LandGuard Stream Reader",
            "pages_count": 1,
            "pages": [{
                "page_number": 1,
                "text": stream_text,
                "confidence": confidence,
                "char_count": len(stream_text)
            }]
        }

    # --- Tier 5: Honest unreadable result (No fake text fabricated) ---
    return {
        "status": "UNREADABLE",
        "text": "[Unreadable Document: No readable text or images could be extracted from the PDF.]",
        "confidence": 0.0,
        "engine": "Document Reader",
        "error": "No readable digital text or OCR images detected in document.",
        "pages_count": 0,
        "pages": []
    }


def process_document_ocr(file_path: str) -> Dict[str, Any]:
    """
    Main universal entrypoint for processing any uploaded document file
    (PDF, PNG, JPG, JPEG, TIFF, BMP).
    """
    if not os.path.exists(file_path):
        return {
            "status": "FAILED",
            "text": "",
            "confidence": 0.0,
            "error": "File not found at path",
            "pages_count": 0,
            "pages": []
        }

    ext = os.path.splitext(file_path)[1].lower()

    if ext in ['.pdf']:
        return extract_text_from_pdf(file_path)
    elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
        return extract_text_from_image(file_path)
    else:
        return {
            "status": "FAILED",
            "text": "",
            "confidence": 0.0,
            "error": f"Unsupported file extension: {ext}",
            "pages_count": 0,
            "pages": []
        }
