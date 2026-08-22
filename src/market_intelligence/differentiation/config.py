from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DifferentiationConfig:
    gap_weights: dict[str, float] = field(
        default_factory=lambda: {
            "feature_gap": 0.25,
            "complaint_gap": 0.15,
            "product_depth_gap": 0.15,
            "customization_gap": 0.10,
            "automation_gap": 0.10,
            "ux_gap": 0.08,
            "visual_quality_gap": 0.06,
            "documentation_gap": 0.06,
            "internationalization_gap": 0.03,
            "positioning_gap": 0.02,
        }
    )
    modern_feature_terms: tuple[str, ...] = (
        "dashboard",
        "automation",
        "workflow",
        "api",
        "erp",
        "sync",
        "forecast",
        "analytics",
        "integration",
        "custom",
        "brand",
        "onboarding",
        "international",
        "localization",
        "multi-currency",
        "document",
        "templates",
        "chat",
        "ai",
    )
    basic_tool_terms: tuple[str, ...] = (
        "simple",
        "basic",
        "quick",
        "calculator",
        "helper",
        "template",
        "estimate",
        "margin",
        "pricing",
        "sheet",
    )
    complaint_terms: tuple[str, ...] = (
        "manual",
        "painful",
        "slow",
        "limited",
        "annoying",
        "frustrating",
        "missing",
        "poor",
        "hard",
        "no",
        "lack",
        "clunky",
    )
    model_version: str = "differentiation-v1"
