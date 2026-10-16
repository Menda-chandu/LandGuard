"""
LandGuard Image Preprocessing & Quality Enhancement Module.
Applies computer vision filters (deskewing, contrast enhancement, denoising,
and orientation correction) to maximize OCR extraction quality on scanned deeds.
"""

import math
import logging
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

logger = logging.getLogger("landguard.ocr.preprocessor")


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """Converts a PIL Image to an OpenCV BGR/Grayscale numpy array."""
    np_img = np.array(pil_image)
    if len(np_img.shape) == 2:
        return np_img  # already grayscale
    elif len(np_img.shape) == 3 and np_img.shape[2] == 4:
        return cv2.cvtColor(np_img, cv2.COLOR_RGBA2BGR) if cv2 else np_img
    elif len(np_img.shape) == 3 and np_img.shape[2] == 3:
        return cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR) if cv2 else np_img
    return np_img


def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
    """Converts an OpenCV image array to a PIL Image."""
    if len(cv2_image.shape) == 2:
        return Image.fromarray(cv2_image)
    elif cv2_image.shape[2] == 3:
        rgb = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB) if cv2 else cv2_image
        return Image.fromarray(rgb)
    return Image.fromarray(cv2_image)


def detect_skew_angle(cv2_gray: np.ndarray) -> float:
    """
    Computes skew angle (degrees) using minimum bounding box of thresholded text contours.
    """
    if cv2 is None or cv2_gray is None:
        return 0.0

    try:
        # Invert: text should be white, background black
        _, thresh = cv2.threshold(cv2_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 100:
            return 0.0

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
        else:
            angle = -angle

        # Cap corrections to realistic document skew
        if abs(angle) > 25.0:
            return 0.0

        return float(angle)
    except Exception as e:
        logger.debug(f"Skew detection notice: {e}")
        return 0.0


def rotate_image(cv2_img: np.ndarray, angle: float) -> np.ndarray:
    """Rotates an OpenCV image by angle degrees around its center."""
    if cv2 is None or abs(angle) < 0.5:
        return cv2_img

    try:
        (h, w) = cv2_img.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            cv2_img,
            matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        return rotated
    except Exception as e:
        logger.debug(f"Image rotation notice: {e}")
        return cv2_img


def check_and_fix_orientation(pil_image: Image.Image) -> Image.Image:
    """
    Detects 90, 180, or 270 degree rotation via Tesseract OSD and corrects it.
    """
    if not pytesseract:
        return pil_image

    try:
        osd = pytesseract.image_to_osd(pil_image, output_type=pytesseract.Output.DICT)
        rotate_deg = osd.get("rotate", 0)
        conf = float(osd.get("orientation_conf", 0.0))
        if rotate_deg in [90, 180, 270] and conf >= 10.0:
            logger.info(f"Correcting image orientation by {rotate_deg} degrees (confidence: {conf})")
            return pil_image.rotate(-rotate_deg, expand=True)
    except Exception:
        pass

    return pil_image


def enhance_document_image(pil_image: Image.Image) -> Image.Image:
    """
    Gentle contrast enhancement and deskewing that preserves fine font strokes:
    1. Grayscale conversion.
    2. Optional deskew if angle > 0.8 degrees.
    3. Mild contrast enhancement and sharpening without erosive blur filters.
    """
    try:
        # Check orientation
        img = check_and_fix_orientation(pil_image)

        # Deskew if OpenCV is present
        if cv2 is not None:
            cv_img = pil_to_cv2(img)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY) if len(cv_img.shape) == 3 else cv_img
            angle = detect_skew_angle(gray)
            if abs(angle) >= 0.8:
                gray = rotate_image(gray, angle)
                img = Image.fromarray(gray)

        # Apply mild contrast boost and sharpening
        gray_pil = img.convert('L')
        enhancer = ImageEnhance.Contrast(gray_pil)
        enhanced = enhancer.enhance(1.8)
        sharpened = enhanced.filter(ImageFilter.SHARPEN)
        return sharpened

    except Exception as e:
        logger.warning(f"Image enhancement warning: {e}. Preserving original image.")
        return pil_image
