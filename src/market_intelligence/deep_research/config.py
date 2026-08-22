from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DeepResearchConfig:
    deep_research_count: int = 25
    leader_count: int = 5
    mid_market_count: int = 5
    emerging_count: int = 5
    research_data_max_age_days: int = 30
    review_sample_size: int = 30
    price_segment_bias: float = 0.15
    model_version: str = "deep-research-v1"
    buyer_group_targets: dict[str, int] = field(default_factory=lambda: {
        "small_business": 30,
        "creators": 20,
        "independent_professionals": 15,
        "property_hospitality": 10,
        "ecommerce_sellers": 10,
        "monetized_hobbies": 10,
        "professional_productivity": 5,
        "other": 5,
    })


def default_deep_research_config() -> DeepResearchConfig:
    return DeepResearchConfig()
