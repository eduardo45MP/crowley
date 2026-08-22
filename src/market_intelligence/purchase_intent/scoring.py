from __future__ import annotations

from market_intelligence.purchase_intent.config import PurchaseIntentConfig
from market_intelligence.purchase_intent.models import PurchaseIntentFeatures


class PurchaseIntentScorer:
    def __init__(self, config: PurchaseIntentConfig | None = None) -> None:
        self.config = config or PurchaseIntentConfig()

    def score(self, features: PurchaseIntentFeatures) -> tuple[float, float, float, dict[str, float], dict[str, float], dict[str, float]]:
        components = {
            "financial_impact": float(features.financial_impact_score or 0.0),
            "usage_frequency": float(features.usage_frequency_score or 0.0),
            "cost_of_error": float(features.cost_of_error_score or 0.0),
            "urgency": float(features.urgency_score or 0.0),
            "perceived_value": float(features.perceived_value_score or 0.0),
            "commercial_context": float(features.commercial_context_score or 0.0),
            "workflow_criticality": float(features.workflow_criticality_score or 0.0),
            "repeatability": float(features.repeatability_score or 0.0),
            "replacement_cost": float(features.replacement_cost_score or 0.0),
        }
        weights = {
            "financial_impact": 0.25,
            "usage_frequency": 0.15,
            "cost_of_error": 0.20,
            "urgency": 0.10,
            "perceived_value": 0.15,
            "commercial_context": 0.05,
            "workflow_criticality": 0.05,
            "repeatability": 0.05,
            "replacement_cost": 0.05,
        }

        available_components = {key: value for key, value in components.items() if value > 0}
        coverage = min(1.0, len(available_components) / len(components))
        weighted_total = sum(value * weights[key] for key, value in components.items())
        total_weight = sum(weights.values())
        base_score = max(0.0, min(100.0, (weighted_total / total_weight)))

        llm_penalty = min(self.config.llm_penalty_max, (features.llm_substitutability or 0.0) * 0.15)
        free_alt_penalty = min(self.config.free_alternative_penalty_max, (features.free_alternative_pressure or 0.0) * 0.12)
        penalties = {
            "llm_substitutability": round(llm_penalty, 4),
            "free_alternative_pressure": round(free_alt_penalty, 4),
        }
        score = max(0.0, min(100.0, base_score - llm_penalty - free_alt_penalty))

        confidence = min(1.0, coverage * 0.7 + (0.3 if (features.problem_type and features.buyer_type) else 0.15))
        return score, max(0.0, min(1.0, confidence)), coverage, {key: round(value, 4) for key, value in components.items()}, penalties, {key: round(value, 4) for key, value in weights.items()}
