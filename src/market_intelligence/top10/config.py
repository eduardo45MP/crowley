from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Top10SelectionConfig:
    model_version: str = "top10-selection-v1"
    target_size: int = 10
    deep_research_count: int = 25
    minimum_research_coverage: float = 0.65
    minimum_research_confidence: float = 0.60
    max_contradiction_penalty: float = 20.0
    redundancy_penalty: float = 10.0
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "opportunity_score": 0.40,
            "evidence_strength": 0.20,
            "differentiation_clarity": 0.15,
            "thesis_strength": 0.10,
            "product_clarity": 0.10,
            "build_ease": 0.05,
        }
    )
    leader_count: int = 5
    mid_market_count: int = 5
    emerging_count: int = 5


def default_top10_selection_config() -> Top10SelectionConfig:
    return Top10SelectionConfig()
