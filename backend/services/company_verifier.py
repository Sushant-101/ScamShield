
import re
from urllib.parse import urlparse

from services.domain_checker import verify_domain


FREE_EMAIL_PROVIDERS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    " rediffmail.com",
}


def get_domain(value):
    if not value:
        return None

    value = value.strip()

    if "@" in value and "://" not in value:
        return value.rsplit("@", 1)[-1].lower()

    if not value.startswith(("http://", "https://")):
        value = "https://" + value

    parsed = urlparse(value)
    return (parsed.hostname or "").lower().removeprefix("www.") or None


def verify_company(company_name, website=None, email=None):
    result = {
        "company_name": company_name.strip() if company_name else None,
        "website": website,
        "email": email,
        "status": "manual_check_required",
        "checks": {},
        "warnings": [],
        "message": ""
    }

    if not company_name or not company_name.strip():
        result["warnings"].append("Company name was not provided.")
        result["message"] = "Company name is required."
        return result

    # Website check
    website_domain = get_domain(website)

    if website_domain:
        result["checks"]["website_domain"] = website_domain

        try:
            domain_result = verify_domain(website)
            result["checks"]["domain_verification"] = domain_result
        except Exception as exc:
            result["warnings"].append(
                f"Website domain check failed: {str(exc)}"
            )
    else:
        result["warnings"].append("Company website was not provided.")

    # Email check
    email_domain = None

    if email:
        email = email.strip().lower()

        if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            email_domain = email.rsplit("@", 1)[-1]
            result["checks"]["email_format"] = "Valid format"
            result["checks"]["email_domain"] = email_domain

            if email_domain in FREE_EMAIL_PROVIDERS:
                result["warnings"].append(
                    "Email uses a free email provider. "
                    "This does not prove the company is fraudulent."
                )
        else:
            result["checks"]["email_format"] = "Invalid format"
            result["warnings"].append("Email address format is invalid.")

    else:
        result["warnings"].append("Company email was not provided.")

    # Compare website and email domains
    if website_domain and email_domain:
        if website_domain == email_domain:
            result["checks"]["website_email_match"] = True
        else:
            result["checks"]["website_email_match"] = False
            result["warnings"].append(
                "Email domain does not match the company website domain."
            )

    result["status"] = "basic_checks_completed"
    result["message"] = (
        "Basic company details have been checked. "
        "Official company registration has not been confirmed."
    )

    return result
