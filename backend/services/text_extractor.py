"""
ScamShield - Text Extractor Service

Central text extraction service.

Supported:
- TXT
- PDF
- Images

PDF files are handled by pdf_analyzer.py.
Image files are handled by ocr_service.py.
"""

from pathlib import Path
from typing import Any, Dict

from services.pdf_analyzer import extract_text_from_pdf
from services.ocr_service import extract_text_from_image


# ------------------------------------------------------------
# Supported File Types
# ------------------------------------------------------------

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".log",
}

PDF_EXTENSIONS = {
    ".pdf",
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tiff",
    ".tif",
}


# ------------------------------------------------------------
# Plain Text Extraction
# ------------------------------------------------------------

def extract_text_file(file_path: str) -> Dict[str, Any]:
    """Extract text from a normal text file."""

    try:
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "text": "",
                "file_type": "text",
                "message": "Text file not found.",
            }

        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).strip()

        if not text:
            return {
                "success": False,
                "text": "",
                "file_type": "text",
                "message": "The text file is empty.",
            }

        return {
            "success": True,
            "text": text,
            "file_type": "text",
            "message": "Text extracted successfully.",
        }

    except Exception as exc:
        return {
            "success": False,
            "text": "",
            "file_type": "text",
            "message": f"Failed to read text file: {str(exc)}",
        }


# ------------------------------------------------------------
# Main Extraction Function
# ------------------------------------------------------------

def extract_text_from_file(file_path: str) -> Dict[str, Any]:
    """
    Automatically extract text based on file extension.

    Supported:
        TXT / MD / CSV / LOG
        PDF
        JPG / JPEG / PNG / WEBP / BMP / TIFF
    """

    try:
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "text": "",
                "file_type": "unknown",
                "message": "File not found.",
            }

        extension = path.suffix.lower()

        # ----------------------------------------------------
        # Text File
        # ----------------------------------------------------

        if extension in TEXT_EXTENSIONS:
            return extract_text_file(file_path)

        # ----------------------------------------------------
        # PDF File
        # ----------------------------------------------------

        if extension in PDF_EXTENSIONS:
            result = extract_text_from_pdf(file_path)

            return {
                **result,
                "file_type": "pdf",
            }

        # ----------------------------------------------------
        # Image File
        # ----------------------------------------------------

        if extension in IMAGE_EXTENSIONS:
            result = extract_text_from_image(file_path)

            return {
                **result,
                "file_type": "image",
            }

        # ----------------------------------------------------
        # Unsupported File
        # ----------------------------------------------------

        return {
            "success": False,
            "text": "",
            "file_type": "unknown",
            "message": (
                f"Unsupported file type: {extension or 'unknown'}. "
                "Supported files are TXT, PDF and common image formats."
            ),
        }

    except Exception as exc:
        return {
            "success": False,
            "text": "",
            "file_type": "unknown",
            "message": f"Text extraction failed: {str(exc)}",
        }


# ------------------------------------------------------------
# Simple Compatibility Wrapper
# ------------------------------------------------------------

def get_text(file_path: str) -> str:
    """
    Return only extracted text.

    Useful when another service only needs the text.
    """

    result = extract_text_from_file(file_path)

    if not result["success"]:
        return ""

    return result["text"]