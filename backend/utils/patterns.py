"""
ScamShield - Fraud Detection Patterns

This file contains the fraud/scam patterns used by the
ScamShield analysis engine.

The patterns are intentionally kept separate from the
detection logic so they can be updated easily later.
"""

# ============================================================
# 1. FINANCIAL / UPFRONT FEE PATTERNS
# ============================================================

FINANCIAL_PATTERNS = [
    {
        "name": "Registration Fee",
        "category": "Financial Demand",
        "severity": "High",
        "score": 20,
        "patterns": [
            r"\bregistration\s+fee\b",
            r"\bregistration\s+charge\b",
            r"\bpay\s+(?:a\s+)?registration\b",
            r"\bregistration\s+amount\b",
        ],
        "explanation": "Requests for upfront registration payments can be a common job-scam indicator.",
    },
    {
        "name": "Training Fee",
        "category": "Financial Demand",
        "severity": "High",
        "score": 18,
        "patterns": [
            r"\btraining\s+fee\b",
            r"\btraining\s+charge\b",
            r"\bpay\s+(?:for\s+)?training\b",
            r"\btraining\s+amount\b",
        ],
        "explanation": "A job offer requesting payment for mandatory training is a risk indicator.",
    },
    {
        "name": "Processing Fee",
        "category": "Financial Demand",
        "severity": "High",
        "score": 18,
        "patterns": [
            r"\bprocessing\s+fee\b",
            r"\bprocessing\s+charge\b",
            r"\bpay\s+(?:the\s+)?processing\s+fee\b",
            r"\bapplication\s+processing\s+fee\b",
        ],
        "explanation": "Requests for job application or processing fees should be treated cautiously.",
    },
    {
        "name": "Security Deposit",
        "category": "Financial Demand",
        "severity": "High",
        "score": 20,
        "patterns": [
            r"\bsecurity\s+deposit\b",
            r"\bsecurity\s+amount\b",
            r"\brefundable\s+deposit\b",
            r"\bpay\s+(?:a\s+)?deposit\b",
        ],
        "explanation": "A security deposit requested before joining can be a suspicious recruitment pattern.",
    },
    {
        "name": "Laptop / Equipment Fee",
        "category": "Financial Demand",
        "severity": "High",
        "score": 18,
        "patterns": [
            r"\blaptop\s+fee\b",
            r"\blaptop\s+charge\b",
            r"\bequipment\s+fee\b",
            r"\bequipment\s+charge\b",
            r"\bpay\s+for\s+(?:the\s+)?laptop\b",
        ],
        "explanation": "Requests for upfront payment for job equipment can indicate recruitment fraud.",
    },
    {
        "name": "Joining Fee",
        "category": "Financial Demand",
        "severity": "High",
        "score": 20,
        "patterns": [
            r"\bjoining\s+fee\b",
            r"\bjoining\s+charge\b",
            r"\bpay\s+(?:a\s+)?joining\s+fee\b",
            r"\bjoining\s+amount\b",
        ],
        "explanation": "A fee demanded before joining a job is a significant warning sign.",
    },
]


# ============================================================
# 2. DIRECT SELECTION / GUARANTEED JOB PATTERNS
# ============================================================

DIRECT_SELECTION_PATTERNS = [
    {
        "name": "Direct Selection",
        "category": "Direct Selection",
        "severity": "Medium",
        "score": 12,
        "patterns": [
            r"\bdirectly\s+selected\b",
            r"\byou\s+are\s+selected\b",
            r"\bselected\s+based\s+on\s+your\s+resume\b",
            r"\bselected\s+without\s+(?:an?\s+)?interview\b",
            r"\bno\s+interview\s+required\b",
        ],
        "explanation": "Selection without a normal interview or hiring process can be suspicious.",
    },
    {
        "name": "Guaranteed Job",
        "category": "Direct Selection",
        "severity": "High",
        "score": 18,
        "patterns": [
            r"\bguaranteed\s+job\b",
            r"\b100\s*%\s+job\b",
            r"\bjob\s+guarantee\b",
            r"\bguaranteed\s+placement\b",
            r"\bguaranteed\s+employment\b",
        ],
        "explanation": "Guaranteed employment claims can be a warning sign, particularly when combined with payment demands.",
    },
]


# ============================================================
# 3. URGENCY / PAYMENT PRESSURE
# ============================================================

URGENCY_PATTERNS = [
    {
        "name": "Urgent Response",
        "category": "Urgency Pressure",
        "severity": "Medium",
        "score": 10,
        "patterns": [
            r"\brespond\s+within\s+\d+\s*(?:hour|hours|hr|hrs)\b",
            r"\breply\s+within\s+\d+\s*(?:hour|hours|hr|hrs)\b",
            r"\bwithin\s+24\s+hours\b",
            r"\bwithin\s+12\s+hours\b",
            r"\bwithin\s+48\s+hours\b",
        ],
        "explanation": "Artificial deadlines can pressure candidates into making quick decisions.",
    },
    {
        "name": "Immediate Payment",
        "category": "Urgency Pressure",
        "severity": "High",
        "score": 15,
        "patterns": [
            r"\bpay\s+immediately\b",
            r"\bmake\s+payment\s+immediately\b",
            r"\bpay\s+now\b",
            r"\bpayment\s+required\s+today\b",
            r"\bpay\s+today\b",
        ],
        "explanation": "Immediate payment demands increase the risk of financial fraud.",
    },
    {
        "name": "Limited Time Pressure",
        "category": "Urgency Pressure",
        "severity": "Medium",
        "score": 8,
        "patterns": [
            r"\blimited\s+time\b",
            r"\blast\s+chance\b",
            r"\bact\s+now\b",
            r"\bdo\s+not\s+delay\b",
            r"\bdeadline\s+today\b",
            r"\boffer\s+expires\b",
        ],
        "explanation": "Strong time pressure can discourage candidates from verifying an offer.",
    },
]


# ============================================================
# 4. UNUSUAL COMMUNICATION CHANNELS
# ============================================================

COMMUNICATION_PATTERNS = [
    {
        "name": "Telegram Communication",
        "category": "Unusual Communication",
        "severity": "Medium",
        "score": 10,
        "patterns": [
            r"\bcontact\s+(?:us\s+)?(?:only\s+)?on\s+telegram\b",
            r"\btelegram\s+only\b",
            r"\bmessage\s+us\s+on\s+telegram\b",
            r"\bcontact\s+via\s+telegram\b",
        ],
        "explanation": "Recruitment handled exclusively through informal messaging channels can require additional verification.",
    },
    {
        "name": "WhatsApp Communication",
        "category": "Unusual Communication",
        "severity": "Medium",
        "score": 8,
        "patterns": [
            r"\bcontact\s+(?:us\s+)?(?:only\s+)?on\s+whatsapp\b",
            r"\bwhatsapp\s+only\b",
            r"\bmessage\s+us\s+on\s+whatsapp\b",
            r"\bcontact\s+via\s+whatsapp\b",
        ],
        "explanation": "WhatsApp-only recruitment communication should be independently verified.",
    },
    {
        "name": "Personal Email Communication",
        "category": "Unusual Communication",
        "severity": "Medium",
        "score": 8,
        "patterns": [
            r"\bcontact\s+me\s+from\s+my\s+personal\s+email\b",
            r"\breply\s+to\s+my\s+personal\s+email\b",
            r"\buse\s+my\s+gmail\b",
            r"\bcontact\s+me\s+on\s+gmail\b",
        ],
        "explanation": "Recruitment communication from personal email accounts should be verified through official company channels.",
    },
]


# ============================================================
# 5. SENSITIVE INFORMATION REQUESTS
# ============================================================

SENSITIVE_INFO_PATTERNS = [
    {
        "name": "OTP Request",
        "category": "Sensitive Information",
        "severity": "High",
        "score": 25,
        "patterns": [
            r"\bshare\s+(?:your\s+)?otp\b",
            r"\bsend\s+(?:your\s+)?otp\b",
            r"\bprovide\s+(?:your\s+)?otp\b",
            r"\botp\s+(?:required|needed)\b",
        ],
        "explanation": "Job recruiters should not require candidates to share OTPs.",
    },
    {
        "name": "UPI PIN Request",
        "category": "Sensitive Information",
        "severity": "High",
        "score": 30,
        "patterns": [
            r"\bshare\s+(?:your\s+)?upi\s+pin\b",
            r"\bsend\s+(?:your\s+)?upi\s+pin\b",
            r"\bprovide\s+(?:your\s+)?upi\s+pin\b",
            r"\benter\s+(?:your\s+)?upi\s+pin\b",
        ],
        "explanation": "A UPI PIN is sensitive financial information and should never be shared with a recruiter.",
    },
    {
        "name": "Bank Details Request",
        "category": "Sensitive Information",
        "severity": "High",
        "score": 25,
        "patterns": [
            r"\bshare\s+(?:your\s+)?bank\s+details\b",
            r"\bsend\s+(?:your\s+)?bank\s+details\b",
            r"\bprovide\s+(?:your\s+)?bank\s+account\b",
            r"\bbank\s+account\s+details\b",
        ],
        "explanation": "Requests for sensitive bank information during recruitment require strong verification.",
    },
    {
        "name": "Card Details Request",
        "category": "Sensitive Information",
        "severity": "High",
        "score": 30,
        "patterns": [
            r"\bshare\s+(?:your\s+)?card\s+details\b",
            r"\bprovide\s+(?:your\s+)?card\s+details\b",
            r"\bcredit\s+card\s+details\b",
            r"\bdebit\s+card\s+details\b",
            r"\bcard\s+number\b",
        ],
        "explanation": "Requests for debit or credit card information are a serious security warning.",
    },
    {
        "name": "Password Request",
        "category": "Sensitive Information",
        "severity": "High",
        "score": 25,
        "patterns": [
            r"\bshare\s+(?:your\s+)?password\b",
            r"\bsend\s+(?:your\s+)?password\b",
            r"\bprovide\s+(?:your\s+)?password\b",
            r"\blogin\s+password\b",
        ],
        "explanation": "Candidates should never share account passwords with recruiters.",
    },
]


# ============================================================
# 6. SUSPICIOUS PAYMENT TERMS
# ============================================================

PAYMENT_PATTERNS = [
    {
        "name": "UPI Payment",
        "category": "Financial Demand",
        "severity": "High",
        "score": 15,
        "patterns": [
            r"\bpay\s+via\s+upi\b",
            r"\bpayment\s+via\s+upi\b",
            r"\bsend\s+money\s+via\s+upi\b",
            r"\btransfer\s+via\s+upi\b",
        ],
        "explanation": "A recruitment offer requesting direct UPI payment should be independently verified.",
    },
    {
        "name": "Advance Payment",
        "category": "Financial Demand",
        "severity": "High",
        "score": 18,
        "patterns": [
            r"\badvance\s+payment\b",
            r"\bpay\s+in\s+advance\b",
            r"\bupfront\s+payment\b",
            r"\bupfront\s+fee\b",
            r"\bpay\s+before\s+joining\b",
        ],
        "explanation": "Upfront payments before employment are an important recruitment-scam warning sign.",
    },
]


# ============================================================
# 7. ALL PATTERNS
# ============================================================

ALL_FRAUD_PATTERNS = (
    FINANCIAL_PATTERNS
    + DIRECT_SELECTION_PATTERNS
    + URGENCY_PATTERNS
    + COMMUNICATION_PATTERNS
    + SENSITIVE_INFO_PATTERNS
    + PAYMENT_PATTERNS
)


# ============================================================
# 8. REGEX EXTRACTION PATTERNS
# ============================================================

EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

PHONE_PATTERN = (
    r"(?<!\d)"
    r"(?:\+91[\s-]?)?"
    r"[6-9]\d{9}"
    r"(?!\d)"
)

URL_PATTERN = (
    r"https?://[^\s<>\"]+"
    r"|www\.[^\s<>\"]+"
    r"|(?<![@\w])(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s<>\"]*)?"
)

# Indian Rupee and common currency amount patterns.
AMOUNT_PATTERN = (
    r"(?:₹\s*[\d,]+(?:\.\d+)?"
    r"|\bINR\s*[\d,]+(?:\.\d+)?"
    r"|\bRs\.?\s*[\d,]+(?:\.\d+)?"
    r"|\$\s*[\d,]+(?:\.\d+)?)"
)


# ============================================================
# 9. SUSPICIOUS EMAIL DOMAIN PATTERNS
# ============================================================

FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "rediffmail.com",
    "protonmail.com",
    "proton.me",
    "icloud.com",
}


# ============================================================
# 10. COMMON SCAM KEYWORDS
# ============================================================

SCAM_KEYWORDS = [
    "registration fee",
    "processing fee",
    "training fee",
    "security deposit",
    "joining fee",
    "laptop fee",
    "advance payment",
    "upfront payment",
    "guaranteed job",
    "direct selection",
    "no interview",
    "urgent payment",
    "pay immediately",
    "otp",
    "upi pin",
    "bank details",
    "card details",
    "password",
    "telegram only",
    "whatsapp only",
]


# ============================================================
# 11. HELPER FUNCTION
# ============================================================

def get_all_patterns():
    """
    Return the complete list of fraud detection patterns.

    This keeps the fraud detector independent from the
    internal organization of this file.
    """
    return ALL_FRAUD_PATTERNS