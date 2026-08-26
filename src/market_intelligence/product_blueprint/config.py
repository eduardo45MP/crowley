from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProductBlueprintConfig:
    model_version: str = "product-blueprint-v1"
    max_sheets: int = 12
    max_formulas: int = 10
    max_optional_features: int = 8
    default_build_hours: float = 8.0
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "buyer_clarity": 0.25,
            "problem_clarity": 0.25,
            "feature_evidence": 0.25,
            "research_confidence": 0.25,
        }
    )


def default_product_blueprint_config() -> ProductBlueprintConfig:
    return ProductBlueprintConfig()
