from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PurchaseIntentConfig:
    frequency_map: dict[str, float] = field(
        default_factory=lambda: {
            "continuous": 100.0,
            "daily": 95.0,
            "weekly": 80.0,
            "monthly": 65.0,
            "quarterly": 45.0,
            "occasional": 30.0,
            "one_time": 20.0,
            "unknown": 50.0,
        }
    )
    problem_priors: dict[str, dict[str, float]] = field(
        default_factory=lambda: {
            "pricing": {"financial_impact": 95.0, "cost_of_error": 92.0, "urgency": 82.0, "usage_frequency": 68.0, "perceived_value": 94.0},
            "costing": {"financial_impact": 92.0, "cost_of_error": 90.0, "urgency": 78.0, "usage_frequency": 72.0, "perceived_value": 92.0},
            "inventory": {"financial_impact": 88.0, "cost_of_error": 86.0, "urgency": 84.0, "usage_frequency": 90.0, "perceived_value": 82.0},
            "commission": {"financial_impact": 90.0, "cost_of_error": 88.0, "urgency": 82.0, "usage_frequency": 78.0, "perceived_value": 80.0},
            "budget": {"financial_impact": 84.0, "cost_of_error": 83.0, "urgency": 70.0, "usage_frequency": 72.0, "perceived_value": 84.0},
            "roi": {"financial_impact": 93.0, "cost_of_error": 84.0, "urgency": 72.0, "usage_frequency": 62.0, "perceived_value": 90.0},
            "planning": {"financial_impact": 48.0, "cost_of_error": 45.0, "urgency": 42.0, "usage_frequency": 58.0, "perceived_value": 60.0},
            "generic": {"financial_impact": 32.0, "cost_of_error": 30.0, "urgency": 28.0, "usage_frequency": 40.0, "perceived_value": 45.0},
        }
    )
    buyer_priors: dict[str, dict[str, float]] = field(
        default_factory=lambda: {
            "business": {"commercial_context": 96.0, "workflow_criticality": 92.0},
            "freelancer": {"commercial_context": 90.0, "workflow_criticality": 86.0},
            "creator": {"commercial_context": 70.0, "workflow_criticality": 62.0},
            "hobbyist": {"commercial_context": 35.0, "workflow_criticality": 38.0},
            "unknown": {"commercial_context": 52.0, "workflow_criticality": 55.0},
        }
    )
    llm_penalty_max: float = 15.0
    free_alternative_penalty_max: float = 12.0
    model_version: str = "purchase-intent-v1"
