"""
Rule-based document classification from normalized OCR text.

Uses keyword frequency scoring: each category has a list of terms; we count how
many distinct keywords appear as substrings in the full text (case-insensitive).
The category with the highest score wins. Ties break by CATEGORY_ORDER (first
listed wins). If the winning score is zero, the document is unclassified.

This is intentionally simple and explainable—not ML. Extend with Comprehend or
custom models later if needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# Routing labels stored in DynamoDB and used for S3 prefixes (except unclassified).
REFERRAL: Final = "referral"
LAB_RESULT: Final = "lab_result"
INSURANCE: Final = "insurance"
AUTHORIZATION: Final = "authorization"
PROGRESS_NOTE: Final = "progress_note"
IMAGING: Final = "imaging"
UNCLASSIFIED: Final = "unclassified"

# Tie-break order when two categories share the same score (higher priority first).
CATEGORY_ORDER: Final[tuple[str, ...]] = (
    REFERRAL,
    AUTHORIZATION,
    INSURANCE,
    LAB_RESULT,
    IMAGING,
    PROGRESS_NOTE,
)

# Keywords per category (lowercase; matched as substrings in normalized text).
KEYWORD_RULES: Final[dict[str, tuple[str, ...]]] = {
    REFERRAL: (
        "referral",
        "referred",
        "specialist",
        "consultation",
        "consult",
        "to see",
        "transfer of care",
    ),
    LAB_RESULT: (
        "laboratory",
        "lab result",
        "specimen",
        "cbc",
        "cmp",
        "lipid panel",
        "hemoglobin",
        "glucose",
        "reference range",
    ),
    INSURANCE: (
        "insurance",
        "policy",
        "subscriber",
        "copay",
        "deductible",
        "claim",
        "payer",
        "member id",
    ),
    AUTHORIZATION: (
        "prior authorization",
        "pre-authorization",
        "authorization",
        "approved",
        "units approved",
        "certification",
    ),
    PROGRESS_NOTE: (
        "progress note",
        "subjective",
        "objective",
        "assessment",
        "plan",
        "soap",
        "clinical note",
        "encounter",
    ),
    IMAGING: (
        "radiology",
        "mri",
        "ct scan",
        "ct ",
        "x-ray",
        "xray",
        "ultrasound",
        "impression",
        "findings",
    ),
}


@dataclass(frozen=True)
class ClassificationResult:
    classification: str
    matched_keywords: tuple[str, ...]
    confidence: float
    scores: dict[str, int]


def normalize_text(text: str) -> str:
    """Lowercase and collapse whitespace for consistent matching."""
    if not text:
        return ""
    return " ".join(text.lower().split())


def classify_document(text: str) -> ClassificationResult:
    """
    Classify document text. Returns UNCLASSIFIED when no keyword matches.
    Confidence is min(1.0, winning_score / max(1, len(KEYWORDS)) for that category).
    """
    normalized = normalize_text(text)
    scores: dict[str, int] = {}
    matched_by_category: dict[str, list[str]] = {}

    for category, keywords in KEYWORD_RULES.items():
        matched: list[str] = []
        for kw in keywords:
            if kw in normalized:
                matched.append(kw)
        # Count distinct keyword hits (substring can match once per keyword entry).
        scores[category] = len(matched)
        matched_by_category[category] = matched

    # Pick best score; tie-break by CATEGORY_ORDER.
    best_category = UNCLASSIFIED
    best_score = 0
    ordered = list(CATEGORY_ORDER) + [
        c for c in scores if c not in CATEGORY_ORDER
    ]
    for category in ordered:
        s = scores.get(category, 0)
        if s > best_score:
            best_score = s
            best_category = category

    if best_score == 0:
        return ClassificationResult(
            classification=UNCLASSIFIED,
            matched_keywords=(),
            confidence=0.0,
            scores=scores,
        )

    keywords_won = tuple(sorted(set(matched_by_category[best_category])))
    key_count = max(1, len(KEYWORD_RULES[best_category]))
    confidence = min(1.0, best_score / key_count)

    return ClassificationResult(
        classification=best_category,
        matched_keywords=keywords_won,
        confidence=round(confidence, 4),
        scores=scores,
    )
