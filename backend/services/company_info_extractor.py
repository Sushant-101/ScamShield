
import re


# ============================================================
# COMPANY INFORMATION EXTRACTION
# ============================================================

def extract_company_info(text):

    if not text or not text.strip():
        return {
            "success": False,
            "company_name": None,
            "website": None,
            "email": None,
            "address": None,
            "missing_fields": [
                "company_name",
                "website",
                "email",
                "address"
            ],
            "extracted_fields_count": 0,
            "message": "No text was provided."
        }

    text = text.strip()

    # --------------------------------------------------------
    # 1. Extract Email
    # --------------------------------------------------------

    email_pattern = (
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    email_match = re.search(email_pattern, text)

    email = email_match.group(0) if email_match else None

    # --------------------------------------------------------
    # 2. Extract Website
    # --------------------------------------------------------

    website_pattern = (
        r"\b(?:https?://|www\.)[^\s<>\"']+"
    )

    website_match = re.search(
        website_pattern,
        text,
        re.IGNORECASE
    )

    website = None

    if website_match:
        website = website_match.group(0).rstrip(
            ".,;:!?)]}"
        )

    # --------------------------------------------------------
    # 3. Extract Company Name
    # --------------------------------------------------------

    company_name = None

    company_patterns = [
        r"(?:company\s*name|organisation\s*name|organization\s*name|employer)\s*[:\-]\s*([^\n\r]+)",

        r"(?:at|with|for)\s+([A-Z][A-Za-z0-9&.,'() -]{2,100}?\b(?:Private Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|LLP|Inc\.?|Corporation|Corp\.?))\b"
    ]

    for pattern in company_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            candidate = match.group(1).strip()

            candidate = re.split(
                r"[\n\r]",
                candidate
            )[0].strip()

            if candidate:
                company_name = candidate
                break

    # --------------------------------------------------------
    # 4. Extract Company Address
    # --------------------------------------------------------

    address = None

    address_patterns = [
        r"(?:registered\s+office\s+address|company\s+address|office\s+address|registered\s+address|address)\s*[:\-]\s*([^\n\r]+)",

        r"(?:office\s+location|company\s+location)\s*[:\-]\s*([^\n\r]+)"
    ]

    for pattern in address_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            candidate = match.group(1).strip()

            if candidate:
                address = candidate
                break

    # --------------------------------------------------------
    # 5. Store Extracted Information
    # --------------------------------------------------------

    extracted_data = {
        "company_name": company_name,
        "website": website,
        "email": email,
        "address": address
    }

    # --------------------------------------------------------
    # 6. Identify Missing Information
    # --------------------------------------------------------

    missing_fields = [
        field
        for field, value in extracted_data.items()
        if not value
    ]

    # --------------------------------------------------------
    # 7. Final Response
    # --------------------------------------------------------

    return {
        "success": True,
        **extracted_data,
        "missing_fields": missing_fields,
        "extracted_fields_count": (
            len(extracted_data) - len(missing_fields)
        ),
        "message": (
            "Company information extraction completed."
            if not missing_fields
            else "Some company information was not found."
        )
    }
