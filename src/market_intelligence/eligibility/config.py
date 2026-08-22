from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class EligibilityConfig:
    minimum_demand_score: float = 30.0
    minimum_demand_confidence: float = 0.40
    minimum_competition_score: float = 20.0
    minimum_differentiation_score: float = 15.0
    minimum_differentiation_confidence: float = 0.70
    minimum_evidence_coverage: float = 0.40
    minimum_opportunity_confidence: float = 0.35
    max_estimated_build_hours: float = 40.0
    review_build_hours: float = 16.0
    allowed_product_types: tuple[str, ...] = (
        "calculator",
        "spreadsheet",
        "tracker",
        "template",
        "planner",
        "tool",
        "sheet",
    )
    restricted_niches: tuple[str, ...] = (
        "medical",
        "healthcare",
        "legal",
        "finance",
        "investment",
        "insurance",
        "gambling",
        "regulated",
    )
    restricted_keywords: tuple[str, ...] = (
        "guaranteed profit",
        "guaranteed roi",
        "guaranteed income",
        "get rich quickly",
        "risk-free returns",
        "medical diagnosis",
        "treatment recommendation",
        "drug dosage",
        "legal outcome",
        "which stocks should i buy",
        "buy the dip",
    )
    risk_taxonomy: dict[str, list[str]] = field(
        default_factory=lambda: {
            "medical": ["diagnosis", "treatment recommendation", "drug dosage", "medical risk assessment"],
            "legal": ["lawsuit settlement recommendation", "legal outcome", "legal advice"],
            "financial": ["investment recommendation", "tax advice", "stock picking"],
            "gambling": ["betting", "casino", "lottery"],
            "regulated": ["medical advice", "legal advice", "investment advice"],
        }
    )
    model_version: str = "eligibility-v1"

    @property
    def restricted_product_types(self) -> set[str]:
        return set(self.allowed_product_types)
