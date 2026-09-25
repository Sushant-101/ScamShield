"""
ScamShield - Fraud Detection Service

This service analyzes job offers, recruitment messages and similar text
for common scam/fraud indicators.

It is intentionally rule-based for the first backend version.
Later, an AI/LLM layer can be added without changing the API response structure.
"""

import re
from typing import Any, Dict, List
from urllib.parse import urlparse


# ============================================================
# Detection Rules
# ============================================================

FINANCIAL_PATTERNS = [
    r"\bregistration\s+fee\b",
    r"\bprocessing\s+fee\b",
    r"\bapplication\s+fee\b",
    r"\bsecurity\s+deposit\b",
    r"\brefundable\s+fee\b",
    r"\bnon[-\s]?refundable\s+fee\b",
    r"\bpay\s+(?:₹|rs\.?|inr|\$)?\s*\d+",
    r"\bpayment\s+(?:of|for)\b",
    r"\badvance\s+payment\b",
    r"\bupfront\s+payment\b",
    r"\bjoining\s+fee\b",
    r"\btraining\s+fee\b",
    r"\binterview\s+fee\b",
    r"\bverification\s+fee\b",
    r"\b(?:upi|gpay|google\s+pay|phonepe|paytm).*(?:pay|payment|send)\b",
    r"\bpay.*(?:upi|gpay|phonepe|paytm)\b",
]

URGENCY_PATTERNS = [
    r"\brespond\s+within\s+\d+\s*(?:hours?|hrs?)\b",
    r"\bwithin\s+\d+\s*(?:hours?|hrs?|minutes?|mins?)\b",
    r"\bimmediately\b",
    r"\burgent\b",
    r"\bact\s+now\b",
    r"\blast\s+chance\b",
    r"\blimited\s+time\b",
    r"\btoday\s+only\b",
    r"\bdeadline\s+today\b",
    r"\bexpire[sd]?\s+(?:today|soon)\b",
    r"\bimmediate\s+joining\b",
    r"\bjoin\s+immediately\b",
]

UNUSUAL_COMMUNICATION_PATTERNS = [
    r"\bcontact\s+(?:only|me\s+only)\s+(?:on|via)\s+(?:telegram|whatsapp)\b",
    r"\bcontact\s+(?:only|me\s+only)\s+(?:through|via)\b",
    r"\btelegram\s+only\b",
    r"\bwhatsapp\s+only\b",
    r"\bpersonal\s+(?:gmail|yahoo|outlook)\b",
    r"\bmessage\s+me\s+on\s+telegram\b",
    r"\bmessage\s+me\s+on\s+whatsapp\b",
]

DIRECT_SELECTION_PATTERNS = [
    r"\bselected\s+based\s+on\s+your\s+resume\b",
    r"\bselected\s+without\s+(?:an?|the)\s+interview\b",
    r"\bno\s+interview\b",
    r"\bdirect\s+selection\b",
    r"\b100%\s+selected\b",
    r"\bguaranteed\s+(?:job|selection|placement)\b",
    r"\bjob\s+guarantee\b",
    r"\binstant\s+selection\b",
]

GENERIC_OFFER_PATTERNS = [
    r"\bdear\s+(?:candidate|applicant)\b",
    r"\bdear\s+job\s+seeker\b",
    r"\bcongratulations.*selected\b",
    r"\byou\s+have\s+been\s+selected\b",
    r"\byou\s+are\s+selected\b",
    r"\bwork\s+from\s+home.*earn\b",
    r"\bearn\s+(?:₹|rs\.?|inr|\$)?\s*\d+.*(?:daily|weekly|monthly)\b",
]

PERSONAL_DATA_PATTERNS = [
    r"\b(?:send|share|provide|submit).*?(?:aadhaar|aadhar)\b",
    r"\b(?:send|share|provide|submit).*?(?:pan\s+card|pan\s+number)\b",
    r"\b(?:send|share|provide|submit).*?(?:bank\s+details|bank\s+account)\b",
    r"\b(?:send|share|provide|submit).*?(?:card\s+details|debit\s+card|credit\s+card)\b",
    r"\b(?:send|share|provide|submit).*?(?:otp|one[-\s]?time\s+password)\b",
    r"\b(?:send|share|provide|submit).*?(?:cvv|upi\s+pin|pin)\b",
]

SUSPICIOUS_DOMAIN_PATTERNS = [
    r"-careers?\.",
    r"-jobs?\.",
    r"-hiring-",
    r"careers?-portal",
    r"job-portal",
    r"recruitment-",
    r"hr-portal",
    r"placement-",
    r"verify-.*-career",
]


# ============================================================
# Helper Functions
# ============================================================

def normalize_text(text: str) -> str:
    """Normalize text before analysis."""

    if not text:
        return ""

    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_evidence(text: str, max_length: int = 140) -> str:
    """Create short evidence text for frontend display."""

    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= max_length:
        return text

    return text[: max_length - 3] + "..."


def find_pattern_matches(
    text: str,
    patterns: List[str],
) -> List[str]:
    """
    Return unique snippets matching the supplied regex patterns.
    """

    matches: List[str] = []

    for pattern in patterns:
        try:
            for match in re.finditer(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                start = max(0, match.start() - 45)
                end = min(len(text), match.end() + 75)

                snippet = clean_evidence(text[start:end])

                if snippet and snippet not in matches:
                    matches.append(snippet)

        except re.error:
            # Ignore a malformed rule rather than crashing the API.
            continue

    return matches


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""

    pattern = r"(?:https?://|www\.)[^\s<>\"]+"

    urls = re.findall(pattern, text, flags=re.IGNORECASE)

    cleaned = []

    for url in urls:
        url = url.rstrip(".,;:!?)]}")

        if url not in cleaned:
            cleaned.append(url)

    return cleaned


def get_domain(url: str) -> str:
    """Extract hostname from URL."""

    try:
        parsed = urlparse(
            url if url.startswith(("http://", "https://")) else f"https://{url}"
        )

        return parsed.netloc.lower().replace("www.", "")

    except Exception:
        return ""


def is_suspicious_domain(domain: str) -> bool:
    """Basic suspicious/lookalike domain heuristic."""

    if not domain:
        return False

    domain = domain.lower()

    for pattern in SUSPICIOUS_DOMAIN_PATTERNS:
        if re.search(pattern, domain, flags=re.IGNORECASE):
            return True

    suspicious_tlds = [
        ".xyz",
        ".top",
        ".click",
        ".work",
        ".live",
        ".site",
        ".online",
        ".icu",
    ]

    if any(domain.endswith(tld) for tld in suspicious_tlds):
        return True

    return False


def detect_email_addresses(text: str) -> List[str]:
    """Extract email addresses."""

    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    emails = re.findall(pattern, text)

    return list(dict.fromkeys(emails))


def detect_phone_numbers(text: str) -> List[str]:
    """Extract Indian-style phone numbers."""

    pattern = r"(?:\+91[\s-]?)?[6-9]\d{9}\b"

    phones = re.findall(pattern, text)

    return list(dict.fromkeys(phones))


def detect_money_amounts(text: str) -> List[str]:
    """Extract common Indian currency amounts."""

    pattern = (
        r"(?:₹|Rs\.?|INR)\s?"
        r"(?:\d{1,3}(?:,\d{2,3})*|\d+)"
        r"(?:\.\d+)?"
    )

    amounts = re.findall(pattern, text, flags=re.IGNORECASE)

    return list(dict.fromkeys(amounts))


def calculate_severity(score: int) -> str:
    """Convert finding score into severity."""

    if score >= 20:
        return "High"

    if score >= 10:
        return "Medium"

    return "Low"


def calculate_risk_level(score: int) -> str:
    """Convert total risk score into human-readable level."""

    if score >= 70:
        return "High Risk"

    if score >= 45:
        return "Medium Risk"

    if score >= 20:
        return "Caution"

    return "Low Risk"


def add_finding(
    findings: List[Dict[str, Any]],
    category: str,
    evidence: str,
    explanation: str,
    score: int,
) -> None:
    """Add a standardized risk finding."""

    findings.append(
        {
            "category": category,
            "detected_text": evidence,
            "evidence": evidence,
            "explanation": explanation,
            "severity": calculate_severity(score),
            "score": score,
        }
    )


# ============================================================
# Main Fraud Detector
# ============================================================

def analyze_text(text: str) -> Dict[str, Any]:
    """
    Analyze recruitment/job-offer text.

    Returns a frontend-friendly JSON-compatible dictionary.
    """

    text = normalize_text(text)

    if not text:
        return {
            "success": False,
            "message": "No text was provided for analysis.",
            "risk_score": 0,
            "risk_level": "Low Risk",
            "red_flags": [],
            "total_checks": 0,
        }

    findings: List[Dict[str, Any]] = []

    # --------------------------------------------------------
    # 1. Financial Demand
    # --------------------------------------------------------

    financial_matches = find_pattern_matches(
        text,
        FINANCIAL_PATTERNS,
    )

    for evidence in financial_matches[:5]:
        add_finding(
            findings=findings,
            category="Financial Demand",
            evidence=evidence,
            explanation=(
                "Requesting upfront payment, registration fees or "
                "other money from a candidate can be a common scam indicator."
            ),
            score=22,
        )

    # --------------------------------------------------------
    # 2. Urgency Pressure
    # --------------------------------------------------------

    urgency_matches = find_pattern_matches(
        text,
        URGENCY_PATTERNS,
    )

    for evidence in urgency_matches[:5]:
        add_finding(
            findings=findings,
            category="Urgency Pressure",
            evidence=evidence,
            explanation=(
                "Artificial urgency can pressure candidates into making "
                "quick decisions without properly verifying the offer."
            ),
            score=14,
        )

    # --------------------------------------------------------
    # 3. Suspicious Communication
    # --------------------------------------------------------

    communication_matches = find_pattern_matches(
        text,
        UNUSUAL_COMMUNICATION_PATTERNS,
    )

    for evidence in communication_matches[:5]:
        add_finding(
            findings=findings,
            category="Unusual Communication",
            evidence=evidence,
            explanation=(
                "Requests to communicate only through informal or "
                "personal channels may require additional verification."
            ),
            score=12,
        )

    # --------------------------------------------------------
    # 4. Direct Selection
    # --------------------------------------------------------

    direct_matches = find_pattern_matches(
        text,
        DIRECT_SELECTION_PATTERNS,
    )

    for evidence in direct_matches[:5]:
        add_finding(
            findings=findings,
            category="Direct Selection",
            evidence=evidence,
            explanation=(
                "Guaranteed or direct selection without a normal "
                "recruitment process can be a warning sign."
            ),
            score=10,
        )

    # --------------------------------------------------------
    # 5. Generic Offer
    # --------------------------------------------------------

    generic_matches = find_pattern_matches(
        text,
        GENERIC_OFFER_PATTERNS,
    )

    for evidence in generic_matches[:5]:
        add_finding(
            findings=findings,
            category="Generic Offer",
            evidence=evidence,
            explanation=(
                "Generic recruitment language without enough "
                "specific company or role information may require verification."
            ),
            score=7,
        )

    # --------------------------------------------------------
    # 6. Personal / Sensitive Information
    # --------------------------------------------------------

    personal_matches = find_pattern_matches(
        text,
        PERSONAL_DATA_PATTERNS,
    )

    for evidence in personal_matches[:5]:
        add_finding(
            findings=findings,
            category="Sensitive Information Request",
            evidence=evidence,
            explanation=(
                "Requests for identity, banking, OTP, PIN or similar "
                "sensitive information should be independently verified."
            ),
            score=20,
        )

    # --------------------------------------------------------
    # 7. URL / Domain Analysis
    # --------------------------------------------------------

    urls = extract_urls(text)
    suspicious_domains = []

    for url in urls:
        domain = get_domain(url)

        if is_suspicious_domain(domain):
            suspicious_domains.append(
                {
                    "url": url,
                    "domain": domain,
                }
            )

            add_finding(
                findings=findings,
                category="Suspicious Domain",
                evidence=url,
                explanation=(
                    "The domain matches patterns commonly associated "
                    "with lookalike, recruitment or suspicious domains. "
                    "Verify the domain through the company's official website."
                ),
                score=18,
            )

    # --------------------------------------------------------
    # Risk Score
    # --------------------------------------------------------

    raw_score = sum(
        int(finding.get("score", 0))
        for finding in findings
    )

    # Maximum score is 100.
    risk_score = min(raw_score, 100)

    risk_level = calculate_risk_level(risk_score)

    # --------------------------------------------------------
    # Category Summary
    # --------------------------------------------------------

    category_summary: Dict[str, Dict[str, Any]] = {}

    for finding in findings:
        category = finding["category"]

        if category not in category_summary:
            category_summary[category] = {
                "category": category,
                "detected": True,
                "issues": 0,
                "severity": "Low",
            }

        category_summary[category]["issues"] += 1

        current_severity = category_summary[category]["severity"]
        finding_severity = finding["severity"]

        severity_order = {
            "Low": 1,
            "Medium": 2,
            "High": 3,
        }

        if (
            severity_order[finding_severity]
            > severity_order[current_severity]
        ):
            category_summary[category]["severity"] = finding_severity

    # --------------------------------------------------------
    # Quick Summary
    # --------------------------------------------------------

    quick_summary = {
        "total_checks_performed": 7,
        "red_flags_detected": len(findings),
        "risk_score": risk_score,
        "risk_level": risk_level,
    }

    # --------------------------------------------------------
    # Safety Recommendations
    # --------------------------------------------------------

    recommendations = []

    categories = {
        finding["category"]
        for finding in findings
    }

    if "Financial Demand" in categories:
        recommendations.append(
            "Do not pay upfront registration, processing or job-related fees."
        )

    if "Suspicious Domain" in categories:
        recommendations.append(
            "Verify the company and recruitment domain through its official website."
        )

    if "Unusual Communication" in categories:
        recommendations.append(
            "Verify the recruiter using an official company communication channel."
        )

    if "Urgency Pressure" in categories:
        recommendations.append(
            "Do not make rushed decisions because of urgent deadlines."
        )

    if "Sensitive Information Request" in categories:
        recommendations.append(
            "Do not share OTP, PIN, CVV, bank details or unnecessary identity documents."
        )

    if "Direct Selection" in categories:
        recommendations.append(
            "Verify the recruitment process before accepting a direct-selection offer."
        )

    if not recommendations:
        recommendations.append(
            "No major scam indicators were detected by the current rule-based checks."
        )

    # --------------------------------------------------------
    # Extracted Information
    # --------------------------------------------------------

    extracted_information = {
        "email_addresses": detect_email_addresses(text),
        "web_links": urls,
        "phone_numbers": detect_phone_numbers(text),
        "monetary_amounts": detect_money_amounts(text),
    }

    # --------------------------------------------------------
    # Final Response
    # --------------------------------------------------------

    return {
        "success": True,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "total_checks": quick_summary["total_checks_performed"],
        "red_flags_count": len(findings),
        "quick_summary": quick_summary,
        "findings": findings,
        "red_flags": findings,
        "category_summary": list(category_summary.values()),
        "suspicious_domains": suspicious_domains,
        "extracted_information": extracted_information,
        "recommendations": recommendations,
        "analysis_type": "rule_based",
    }


# ============================================================
# Compatibility Wrapper
# ============================================================

def detect_fraud(text: str) -> Dict[str, Any]:
    """
    Simple function that can be imported from routes.

    Example:

        from services.fraud_detector import detect_fraud

        result = detect_fraud(job_offer_text)
    """

    return analyze_text(text)


# ============================================================
# Local Testing
# ============================================================

if __name__ == "__main__":

    sample_text = """
    Congratulations! You have been selected based on your resume.

    Your registration fee is ₹5,000.
    Please respond within 24 hours.

    Contact only on Telegram:
    @hr_recruitment

    Visit:
    https://tcs-hiring-portal.com

    Send payment through UPI to confirm your joining.
    """

    result = analyze_text(sample_text)

    print("\n========== ScamShield Analysis ==========\n")

    print(f"Risk Score : {result['risk_score']}/100")
    print(f"Risk Level : {result['risk_level']}")
    print(f"Red Flags  : {result['red_flags_count']}")

    print("\n---------- Findings ----------")

    for index, finding in enumerate(result["findings"], start=1):

        print(f"\n{index}. {finding['category']}")
        print(f"   Evidence    : {finding['evidence']}")
        print(f"   Severity    : {finding['severity']}")
        print(f"   Explanation : {finding['explanation']}")

    print("\n---------- Recommendations ----------")

    for recommendation in result["recommendations"]:
        print(f"- {recommendation}")