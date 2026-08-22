from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SelectionPolicy:
    target_size: int = 100
    minimum_opportunity_score: float = 70.0
    minimum_confidence: float = 0.50
    minimum_evidence_coverage: float = 0.60
    max_category_share: float = 0.25
    max_per_niche: int = 5
    max_problem_share: float = 0.20
    near_duplicate_threshold: float = 0.82
    buyer_group_quotas: dict[str, dict[str, int]] = field(
        default_factory=lambda: {
            "small_business": {"minimum": 15, "target": 20, "maximum": 25},
            "creators": {"minimum": 10, "target": 15, "maximum": 20},
            "independent_professionals": {"minimum": 10, "target": 15, "maximum": 20},
            "property_hospitality": {"minimum": 5, "target": 10, "maximum": 15},
            "ecommerce_sellers": {"minimum": 5, "target": 10, "maximum": 15},
            "monetized_hobbies": {"minimum": 5, "target": 10, "maximum": 15},
            "professional_productivity": {"minimum": 5, "target": 10, "maximum": 15},
            "other": {"minimum": 5, "target": 10, "maximum": 15},
        }
    )
    product_type_targets: dict[str, tuple[float, float]] = field(
        default_factory=lambda: {
            "calculator": (0.35, 0.50),
            "spreadsheet": (0.25, 0.40),
            "tracker": (0.15, 0.30),
            "template": (0.05, 0.20),
        }
    )
    model_version: str = "selection-v1"


def default_selection_policy() -> SelectionPolicy:
    return SelectionPolicy()
