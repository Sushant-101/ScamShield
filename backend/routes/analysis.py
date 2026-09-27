from pathlib import Path
import shutil
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from services.fraud_detector import analyze_text
from services.text_extractor import extract_text_from_file


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"]
)


# ============================================================
# Text Analysis Request
# ============================================================

class AnalysisRequest(BaseModel):
    text: str


# ============================================================
# Text Analysis API
# ============================================================

@router.post("/")
def analyze_offer(request: AnalysisRequest):

    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="No text was provided for analysis."
        )

    result = analyze_text(request.text)

    return {
        "success": True,
        "data": result
    }


# ============================================================
# File Analysis API
# Supports:
# - PDF
# - Images
# - TXT
# - MD
# - CSV
# - LOG
# ============================================================

@router.post("/file")
async def analyze_file(
    file: UploadFile = File(...),
    text: str = Form("")
):
    """
    Analyze an uploaded file.

    If additional text is provided, it is combined
    with the extracted file text.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was selected."
        )

    original_filename = Path(file.filename).name
    extension = Path(original_filename).suffix.lower()

    allowed_extensions = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
        ".tiff",
        ".tif",
        ".txt",
        ".md",
        ".csv",
        ".log",
    }

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Supported files: PDF, JPG, JPEG, PNG, WEBP, "
                "BMP, TIFF, TXT, MD, CSV and LOG."
            )
        )

    temp_path = None

    try:
        # ----------------------------------------------------
        # Create temporary file
        # ----------------------------------------------------

        suffix = extension or ".tmp"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_path = temp_file.name

            shutil.copyfileobj(
                file.file,
                temp_file
            )

        # ----------------------------------------------------
        # Extract text
        # ----------------------------------------------------

        extraction_result = extract_text_from_file(
            temp_path
        )

        if not extraction_result.get("success"):
            raise HTTPException(
                status_code=422,
                detail=extraction_result.get(
                    "message",
                    "Could not extract text from the uploaded file."
                )
            )

        extracted_text = extraction_result.get(
            "text",
            ""
        ).strip()

        # ----------------------------------------------------
        # Combine uploaded text + extracted text
        # ----------------------------------------------------

        additional_text = (text or "").strip()

        if additional_text and extracted_text:
            final_text = (
                f"{additional_text}\n\n"
                f"{extracted_text}"
            )

        elif additional_text:
            final_text = additional_text

        else:
            final_text = extracted_text

        # ----------------------------------------------------
        # Fraud Analysis
        # ----------------------------------------------------

        analysis_result = analyze_text(
            final_text
        )

        return {
            "success": True,
            "filename": original_filename,
            "file_type": extraction_result.get(
                "file_type",
                extension.replace(".", "")
            ),
            "extracted_text": extracted_text,
            "data": analysis_result,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"File analysis failed: {str(exc)}"
        )

    finally:
        # ----------------------------------------------------
        # Remove temporary file
        # ----------------------------------------------------

        if temp_path:
            try:
                Path(temp_path).unlink(
                    missing_ok=True
                )
            except Exception:
                pass