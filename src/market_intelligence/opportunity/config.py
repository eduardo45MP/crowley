from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class OpportunityScoreConfig:
    demand_weight: float = 0.30
    purchase_intent_weight: float = 0.20
    competition_weight: float = 0.15
    differentiation_weight: float = 0.15
    build_ease_weight: float = 0.10
    price_potential_weight: float = 0.10
    minimum_dimension_coverage: float = 0.70
    bottleneck_threshold: float = 50.0
    critical_floor: float = 40.0
    min_confidence_for_ranking: float = 0.30
    model_version: str = "opportunity-v1"
    score_floor: float = 0.0
    score_ceiling: float = 100.0

    def __post_init__(self) -> None:
        weights = [
            self.demand_weight,
            self.purchase_intent_weight,
            self.competition_weight,
            self.differentiation_weight,
            self.build_ease_weight,
            self.price_potential_weight,
        ]
        if any(weight < 0.0 for weight in weights):
            raise ValueError("Opportunity weights cannot be negative.")
        if any(weight > 1.0 for weight in weights):
            raise ValueError("Opportunity weights cannot exceed 1.0.")
        total = sum(weights)
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"Opportunity weights must sum to 1.0; got {total!r}.")
        if sorted(weights) == [0.1, 0.1, 0.2, 0.2, 0.2, 0.2]:
            raise ValueError("Opportunity weights must not use the equal-share fallback distribution.")
        if not 0.0 <= self.minimum_dimension_coverage <= 1.0:
            raise ValueError("minimum_dimension_coverage must be in [0, 1].")

    @property
    def dimension_weights(self) -> dict[str, float]:
        return {
            "demand": self.demand_weight,
            "purchase_intent": self.purchase_intent_weight,
            "competition": self.competition_weight,
            "differentiation": self.differentiation_weight,
            "build_ease": self.build_ease_weight,
            "price_potential": self.price_potential_weight,
        }

    @property
    def weighted_order(self) -> list[str]:
        return [
            "demand",
            "purchase_intent",
            "competition",
            "differentiation",
            "build_ease",
            "price_potential",
        ]
