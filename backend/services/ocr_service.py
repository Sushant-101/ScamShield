"""
ScamShield - OCR Service

Extracts text from images using Tesseract OCR.
"""

from pathlib import Path
from typing import Any, Dict

from PIL import Image, ImageOps
import pytesseract


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

# Windows Tesseract installation path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# ============================================================
# OCR FROM IMAGE
# ============================================================

def extract_text_from_image(file_path: str) -> Dict[str, Any]:
    """
    Extract text from an image using Tesseract OCR.

    Returns:
        {
            "success": True,
            "text": "...",
            "message": "OCR completed successfully."
        }
    """

    try:
        path = Path(file_path)

        # Check file exists
        if not path.exists():
            return {
                "success": False,
                "text": "",
                "message": "Image file not found.",
            }

        # Supported image formats
        allowed_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".bmp",
            ".tiff",
            ".tif",
        }

        if path.suffix.lower() not in allowed_extensions:
            return {
                "success": False,
                "text": "",
                "message": "Unsupported image format.",
            }

        # Open image
        image = Image.open(path)

        # Convert image to RGB
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Convert to grayscale
        image = ImageOps.grayscale(image)

        # Improve contrast
        image = ImageOps.autocontrast(image)

        # Run Tesseract OCR
        text = pytesseract.image_to_string(
            image,
            config="--psm 6"
        )

        # Remove unnecessary spaces
        text = text.strip()

        # No text found
        if not text:
            return {
                "success": False,
                "text": "",
                "message": "No readable text was detected in the image.",
            }

        # Success
        return {
            "success": True,
            "text": text,
            "message": "OCR completed successfully.",
        }

    except Exception as exc:
        return {
            "success": False,
            "text": "",
            "message": f"OCR failed: {str(exc)}",
        }


# ============================================================
# SIMPLE TEXT WRAPPER
# ============================================================

def get_image_text(file_path: str) -> str:
    """
    Returns only extracted text.
    """

    result = extract_text_from_image(file_path)

    if not result["success"]:
        return ""

    return result["text"]