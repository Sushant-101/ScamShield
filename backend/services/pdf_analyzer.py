"""
ScamShield - PDF Analyzer Service

Extracts text from normal PDFs using pypdf.
If the PDF is scanned/image-based, it uses Tesseract OCR.
"""

from pathlib import Path
from typing import Any, Dict
import os
import shutil

from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract
from PIL import ImageOps


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ============================================================
# POPPLER CONFIGURATION
# ============================================================

# Your downloaded Poppler folder
POPPLER_PATH = (
    r"C:\Users\kumar\Downloads"
    r"\Release-26.09.0-0"
    r"\poppler-26.09.0"
    r"\Library"
    r"\bin"
)


# ============================================================
# FIND POPPLER
# ============================================================

def get_poppler_path() -> str | None:
    """
    Find Poppler automatically.

    First checks the configured path.
    Then checks PATH environment variable.
    """

    # --------------------------------------------------------
    # 1. Check configured Poppler path
    # --------------------------------------------------------

    if os.path.exists(POPPLER_PATH):
        pdftoppm = os.path.join(POPPLER_PATH, "pdftoppm.exe")

        if os.path.exists(pdftoppm):
            return POPPLER_PATH

    # --------------------------------------------------------
    # 2. Check Windows PATH
    # --------------------------------------------------------

    pdftoppm_from_path = shutil.which("pdftoppm")

    if pdftoppm_from_path:
        return str(Path(pdftoppm_from_path).parent)

    # --------------------------------------------------------
    # 3. Check common downloaded location
    # --------------------------------------------------------

    downloads = Path.home() / "Downloads"

    possible_paths = [
        downloads
        / "Release-26.09.0-0"
        / "poppler-26.09.0"
        / "Library"
        / "bin",

        downloads
        / "Release-26.09.0-0"
        / "poppler-26.09.0"
        / "Library"
        / "bin",
    ]

    for possible_path in possible_paths:

        pdftoppm = possible_path / "pdftoppm.exe"

        if pdftoppm.exists():
            return str(possible_path)

    return None


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
    """
    Extract text from a PDF.

    Process:
        1. Check PDF file.
        2. Try normal text extraction using pypdf.
        3. If no text is found, convert PDF pages to images.
        4. Run Tesseract OCR on the images.
    """

    try:

        # ====================================================
        # CHECK FILE
        # ====================================================

        path = Path(file_path)

        if not path.exists():

            return {
                "success": False,
                "text": "",
                "pages": 0,
                "message": "PDF file not found.",
            }

        # ====================================================
        # CHECK FILE TYPE
        # ====================================================

        if path.suffix.lower() != ".pdf":

            return {
                "success": False,
                "text": "",
                "pages": 0,
                "message": "The uploaded file is not a PDF.",
            }

        # ====================================================
        # STEP 1
        # NORMAL PDF TEXT EXTRACTION
        # ====================================================

        try:

            reader = PdfReader(str(path))

            total_pages = len(reader.pages)

        except Exception as pdf_error:

            return {
                "success": False,
                "text": "",
                "pages": 0,
                "message": f"Unable to open PDF: {str(pdf_error)}",
            }

        extracted_pages = []

        for page in reader.pages:

            try:

                page_text = page.extract_text() or ""

                if page_text.strip():

                    extracted_pages.append(
                        page_text.strip()
                    )

            except Exception:

                # Continue with remaining pages
                continue

        extracted_text = "\n\n".join(
            extracted_pages
        ).strip()

        # ====================================================
        # NORMAL PDF SUCCESS
        # ====================================================

        if extracted_text:

            return {
                "success": True,
                "text": extracted_text,
                "pages": total_pages,
                "message": "PDF text extracted successfully.",
            }

        # ====================================================
        # STEP 2
        # SCANNED PDF → OCR
        # ====================================================

        # Find Poppler
        poppler_path = get_poppler_path()

        if not poppler_path:

            return {
                "success": False,
                "text": "",
                "pages": total_pages,
                "message": (
                    "Poppler was not found. "
                    "Please check the Poppler installation."
                ),
            }

        # ====================================================
        # CHECK TESSERACT
        # ====================================================

        if not os.path.exists(TESSERACT_PATH):

            return {
                "success": False,
                "text": "",
                "pages": total_pages,
                "message": (
                    "Tesseract OCR was not found at: "
                    f"{TESSERACT_PATH}"
                ),
            }

        # ====================================================
        # CONVERT PDF → IMAGES
        # ====================================================

        try:

            images = convert_from_path(
                str(path),
                dpi=200,
                fmt="png",
                poppler_path=poppler_path,
            )

        except Exception as conversion_error:

            return {
                "success": False,
                "text": "",
                "pages": total_pages,
                "message": (
                    "PDF to image conversion failed: "
                    f"{str(conversion_error)}"
                ),
            }

        # ====================================================
        # OCR EACH PAGE
        # ====================================================

        ocr_pages = []

        for page_number, image in enumerate(
            images,
            start=1
        ):

            try:

                # --------------------------------------------
                # Convert to grayscale
                # --------------------------------------------

                image = image.convert("L")

                # --------------------------------------------
                # Improve contrast
                # --------------------------------------------

                image = ImageOps.autocontrast(image)

                # --------------------------------------------
                # Run Tesseract OCR
                # --------------------------------------------

                page_text = pytesseract.image_to_string(
                    image,
                    config="--psm 6",
                )

                if page_text.strip():

                    ocr_pages.append(
                        page_text.strip()
                    )

            except Exception:

                # Continue with next page
                continue

        # ====================================================
        # COMBINE OCR TEXT
        # ====================================================

        ocr_text = "\n\n".join(
            ocr_pages
        ).strip()

        # ====================================================
        # OCR SUCCESS
        # ====================================================

        if ocr_text:

            return {
                "success": True,
                "text": ocr_text,
                "pages": total_pages,
                "message": (
                    "Text extracted from scanned PDF "
                    "using OCR."
                ),
            }

        # ====================================================
        # OCR FOUND NOTHING
        # ====================================================

        return {
            "success": False,
            "text": "",
            "pages": total_pages,
            "message": (
                "No readable text was found in the PDF."
            ),
        }

    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as exc:

        return {
            "success": False,
            "text": "",
            "pages": 0,
            "message": (
                f"Failed to analyze PDF: {str(exc)}"
            ),
        }


# ============================================================
# COMPATIBILITY WRAPPER
# ============================================================

def get_pdf_text(file_path: str) -> str:
    """
    Returns only the extracted PDF text.
    """

    result = extract_text_from_pdf(file_path)

    if not result["success"]:
        return ""

    return result["text"]