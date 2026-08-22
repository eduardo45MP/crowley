from __future__ import annotations

INELIGIBLE_PROBLEM_PATTERNS = {
    "regulated_medical_advice": [
        "diagnosis",
        "treatment recommendation",
        "drug dosage",
        "medical risk assessment",
        "insulin dose",
        "medical advice",
    ],
    "regulated_legal_advice": [
        "lawsuit settlement recommendation",
        "legal outcome",
        "legal advice",
        "case strategy",
    ],
    "regulated_financial_advice": [
        "investment recommendation",
        "stock picker",
        "which stocks should i buy",
        "tax advice",
    ],
    "misleading_financial_claims": [
        "guaranteed profit",
        "guaranteed roi",
        "guaranteed income",
        "get rich quickly",
        "risk-free returns",
    ],
}

ALLOWED_PRODUCT_TYPES = {
    "calculator",
    "spreadsheet",
    "tracker",
    "template",
    "planner",
    "tool",
    "sheet",
}

OUT_OF_SCOPE_PRODUCT_TYPES = {
    "course",
    "ebook",
    "full saas",
    "mobile app",
    "mobile game",
    "online course",
    "software platform",
    "service",
}
