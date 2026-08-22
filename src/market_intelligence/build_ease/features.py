from __future__ import annotations

import re

from crawler.clustering import ProductCluster
from market_intelligence.build_ease.models import BuildEaseFeatures


class BuildEaseFeatureExtractor:
    def extract(self, cluster: ProductCluster) -> BuildEaseFeatures:
        text = " ".join([
            cluster.name or "",
            cluster.primary_problem or "",
            *(cluster.keywords or []),
            *(cluster.secondary_problems or []),
        ]).lower()

        tab_count = self._tab_count(cluster, text)
        formula_difficulty = self._formula_difficulty(cluster, text)
        api_dependency = self._api_dependency(cluster, text)
        external_data_need = self._external_data_need(cluster, text)
        design_complexity = self._design_complexity(cluster, text)
        maintenance_need = self._maintenance_need(cluster, text)

        notes = []
        if tab_count >= 4:
            notes.append("multiple tabs required")
        if formula_difficulty >= 70:
            notes.append("complex formulas")
        if api_dependency >= 60:
            notes.append("external integrations")
        if external_data_need >= 60:
            notes.append("data source dependency")
        if design_complexity >= 60:
            notes.append("high design workload")
        if maintenance_need >= 60:
            notes.append("ongoing maintenance burden")

        return BuildEaseFeatures(
            tab_count=tab_count,
            formula_difficulty=formula_difficulty,
            api_dependency=api_dependency,
            external_data_need=external_data_need,
            design_complexity=design_complexity,
            maintenance_need=maintenance_need,
            notes=notes,
        )

    @staticmethod
    def _tab_count(cluster: ProductCluster, text: str) -> float:
        candidate_terms = ["dashboard", "tracker", "planner", "forecast", "inventory", "calculator", "pricing", "erp", "api"]
        matches = sum(1 for term in candidate_terms if term in text)
        return min(100.0, max(10.0, 20.0 + matches * 18.0 + (cluster.product_count - 1) * 10.0))

    @staticmethod
    def _formula_difficulty(cluster: ProductCluster, text: str) -> float:
        formula_signals = ["forecast", "margin", "pricing", "inventory", "commission", "roi", "tax", "variance", "scenario", "optimizer"]
        signals = sum(1 for term in formula_signals if term in text)
        return min(100.0, 15.0 + signals * 18.0 + (cluster.product_count * 4.0))

    @staticmethod
    def _api_dependency(cluster: ProductCluster, text: str) -> float:
        api_terms = ["api", "erp", "sheet", "sync", "integration", "import", "export", "oauth", "webhook"]
        matches = sum(1 for term in api_terms if term in text)
        return min(100.0, 10.0 + matches * 22.0)

    @staticmethod
    def _external_data_need(cluster: ProductCluster, text: str) -> float:
        data_terms = ["forecast", "market", "inventory", "weather", "price", "supplier", "erp", "api", "external"]
        matches = sum(1 for term in data_terms if term in text)
        return min(100.0, 12.0 + matches * 18.0)

    @staticmethod
    def _design_complexity(cluster: ProductCluster, text: str) -> float:
        design_terms = ["dashboard", "visual", "ux", "interface", "brand", "theme", "workflow", "automation"]
        matches = sum(1 for term in design_terms if term in text)
        return min(100.0, 8.0 + matches * 20.0 + (cluster.product_count * 3.0))

    @staticmethod
    def _maintenance_need(cluster: ProductCluster, text: str) -> float:
        maintenance_terms = ["sync", "forecast", "api", "inventory", "automation", "maintain", "update", "pricing"]
        matches = sum(1 for term in maintenance_terms if term in text)
        return min(100.0, 10.0 + matches * 16.0)
