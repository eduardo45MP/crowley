from __future__ import annotations

from crawler.clustering import ProductCluster
from market_intelligence.differentiation.config import DifferentiationConfig
from market_intelligence.differentiation.models import DifferentiationFeatures


class DifferentiationFeatureExtractor:
    def __init__(self, config: DifferentiationConfig | None = None) -> None:
        self.config = config or DifferentiationConfig()

    def extract(self, cluster: ProductCluster) -> DifferentiationFeatures:
        text = " ".join([
            cluster.name or "",
            cluster.primary_problem or "",
            *(cluster.keywords or []),
            *(cluster.secondary_problems or []),
        ]).lower()

        modern_signals = sum(1 for term in self.config.modern_feature_terms if term in text)
        basic_signals = sum(1 for term in self.config.basic_tool_terms if term in text)
        complaint_signals = sum(1 for term in self.config.complaint_terms if term in text)
        product_depth = 1 if any(term in text for term in ("inventory", "forecast", "dashboard", "tracker", "automation")) else 0

        modern_penalty = max(0.0, modern_signals * 12.0)
        feature_gap = self._clamp(35.0 + (basic_signals * 18.0) + max(0, 6 - modern_signals) * 10.0 + (0.0 if product_depth else 12.0) - modern_penalty)
        complaint_gap = self._clamp(25.0 + complaint_signals * 12.0 + max(0, 3 - modern_signals) * 8.0 - modern_penalty * 0.5)
        product_depth_gap = self._clamp(30.0 + max(0, 2 - product_depth) * 22.0 + max(0, 3 - modern_signals) * 9.0 - modern_penalty * 0.4)
        customization_gap = self._clamp(30.0 + (0 if "custom" in text else 25.0) + (0 if "workflow" in text else 15.0) + max(0, 2 - modern_signals) * 6.0 - modern_signals * 8.0)
        automation_gap = self._clamp(25.0 + (0 if any(term in text for term in ("automation", "api", "sync", "workflow", "export", "import")) else 30.0) + max(0, 2 - modern_signals) * 12.0 - modern_signals * 10.0)
        ux_gap = self._clamp(30.0 + (0 if any(term in text for term in ("dashboard", "workflow", "ux", "onboarding", "experience")) else 28.0) - modern_signals * 8.0)
        visual_quality_gap = self._clamp(25.0 + (0 if any(term in text for term in ("brand", "design", "theme", "visual", "dashboard")) else 30.0) - modern_signals * 7.0)
        documentation_gap = self._clamp(20.0 + (0 if any(term in text for term in ("docs", "documentation", "guide", "tutorial", "onboarding", "template")) else 28.0) + max(0, 2 - modern_signals) * 8.0 - modern_signals * 6.0)
        internationalization_gap = self._clamp(10.0 + (0 if any(term in text for term in ("international", "localization", "multi-currency", "region", "locale", "tax")) else 35.0) - modern_signals * 4.0)
        positioning_gap = self._clamp(20.0 + (0 if any(term in text for term in ("brand", "premium", "platform", "suite", "studio", "os")) else 30.0) + (0 if cluster.product_count and cluster.product_count > 2 else 18.0) - modern_signals * 4.0)

        notes: list[str] = []
        for name, value in {
            "feature_gap": feature_gap,
            "complaint_gap": complaint_gap,
            "product_depth_gap": product_depth_gap,
            "customization_gap": customization_gap,
            "automation_gap": automation_gap,
            "ux_gap": ux_gap,
            "visual_quality_gap": visual_quality_gap,
            "documentation_gap": documentation_gap,
            "internationalization_gap": internationalization_gap,
            "positioning_gap": positioning_gap,
        }.items():
            if value >= 70:
                notes.append(name)

        return DifferentiationFeatures(
            feature_gap=feature_gap,
            complaint_gap=complaint_gap,
            product_depth_gap=product_depth_gap,
            customization_gap=customization_gap,
            automation_gap=automation_gap,
            ux_gap=ux_gap,
            visual_quality_gap=visual_quality_gap,
            documentation_gap=documentation_gap,
            internationalization_gap=internationalization_gap,
            positioning_gap=positioning_gap,
            notes=notes,
        )

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(100.0, value))
