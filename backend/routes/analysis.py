
from pathlib import Path
import shutil
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from services.fraud_detector import analyze_text
from services.text_extractor import extract_text_from_file
from services.domain_checker import verify_domain
from services.company_verifier import verify_company
from services.address_verifier import verify_address
from services.company_info_extractor import extract_company_info


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"]
)


# ============================================================
# DOMAIN VERIFICATION
# ============================================================

def add_domain_verification(result):

    urls = result.get(
        "extracted_information", {}
    ).get("web_links", [])

    domain_results = []

    unique_urls = list(dict.fromkeys(urls))

    for url in unique_urls:
        try:
            verification = verify_domain(url)
            domain_results.append(verification)

        except Exception as exc:
            domain_results.append({
                "url": url,
                "error": str(exc)
            })

    result["domain_verification"] = domain_results

    return result


# ============================================================
# COMPANY + ADDRESS VERIFICATION
# ============================================================

def add_company_verifications(
    result,
    text,
    company_name=None,
    website=None,
    email=None,
    address=None
):

    # --------------------------------------------------------
    # 1. Extract company information from text
    # --------------------------------------------------------

    extracted = extract_company_info(text)

    # --------------------------------------------------------
    # 2. Combine extracted information and user input
    # User-provided values take priority
    # --------------------------------------------------------

    company_details = {
        "company_name": company_name or extracted.get("company_name"),
        "website": website or extracted.get("website"),
        "email": email or extracted.get("email"),
        "address": address or extracted.get("address")
    }

    missing_fields = [
        field
        for field, value in company_details.items()
        if not value or not str(value).strip()
    ]

    # --------------------------------------------------------
    # 3. Company Verification
    # --------------------------------------------------------

    if company_details["company_name"]:

        company_result = verify_company(
            company_details["company_name"],
            website=company_details["website"],
            email=company_details["email"]
        )

    else:

        company_result = {
            "status": "missing_information",
            "message": "Company name is required.",
            "warnings": []
        }

    # --------------------------------------------------------
    # 4. Address Verification
    # MCA is not used.
    # No official registered-address source is connected yet.
    # --------------------------------------------------------

    if company_details["address"]:

        address_result = verify_address(
            company_details["address"],
            registered_address=None
        )

    else:

        address_result = {
            "status": "missing_information",
            "message": "Company address is required.",
            "warnings": []
        }

    # --------------------------------------------------------
    # 5. Add results to main analysis
    # --------------------------------------------------------

    result["company_information"] = {
        **company_details,
        "extraction_success": extracted.get("success", False),
        "extracted_fields": extracted,
        "missing_fields": missing_fields
    }

    result["company_verification"] = company_result
    result["address_verification"] = address_result

    return result


# ============================================================
# TEXT ANALYSIS REQUEST
# ============================================================

class AnalysisRequest(BaseModel):

    text: str

    company_name: str | None = None
    website: str | None = None
    email: str | None = None
    address: str | None = None


# ============================================================
# COMMON ANALYSIS FUNCTION
# ============================================================

def perform_analysis(
    text,
    company_name=None,
    website=None,
    email=None,
    address=None
):

    # Existing fraud detection
    result = analyze_text(text)

    # Existing domain verification
    result = add_domain_verification(result)

    # Company information and verification
    result = add_company_verifications(
        result=result,
        text=text,
        company_name=company_name,
        website=website,
        email=email,
        address=address
    )

    return result


# ============================================================
# TEXT ANALYSIS API
# ============================================================

@router.post("/")
def analyze_offer(request: AnalysisRequest):

    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="No text was provided for analysis."
        )

    result = perform_analysis(
        text=request.text,
        company_name=request.company_name,
        website=request.website,
        email=request.email,
        address=request.address
    )

    return {
        "success": True,
        "data": result
    }


# ============================================================
# FILE ANALYSIS API
# Supports PDF, Images, TXT, MD, CSV and LOG
# ============================================================

@router.post("/file")
async def analyze_file(
    file: UploadFile = File(...),
    text: str = Form(""),
    company_name: str | None = Form(None),
    website: str | None = Form(None),
    email: str | None = Form(None),
    address: str | None = Form(None)
):

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
        # Combine uploaded text and extracted text
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

        if not final_text.strip():
            raise HTTPException(
                status_code=422,
                detail="No readable text was found."
            )

        # ----------------------------------------------------
        # Run complete analysis
        # ----------------------------------------------------

        analysis_result = perform_analysis(
            text=final_text,
            company_name=company_name,
            website=website,
            email=email,
            address=address
        )

        return {
            "success": True,
            "filename": original_filename,
            "file_type": extraction_result.get(
                "file_type",
                extension.replace(".", "")
            ),
            "extracted_text": extracted_text,
            "data": analysis_result
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
