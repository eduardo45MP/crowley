from __future__ import annotations

from collections import Counter

from crawler.clustering import ProductCluster
from market_intelligence.purchase_intent.config import PurchaseIntentConfig
from market_intelligence.purchase_intent.models import PurchaseIntentFeatures


class PurchaseIntentFeatureExtractor:
    def __init__(self, config: PurchaseIntentConfig | None = None) -> None:
        self.config = config or PurchaseIntentConfig()

    def extract(self, cluster: ProductCluster) -> PurchaseIntentFeatures:
        problem_type = self._resolve_problem_type(cluster)
        buyer_type = self._resolve_buyer_type(cluster)
        workflow_trigger = self._resolve_workflow_trigger(problem_type, cluster)
        consequences = self._resolve_consequences(problem_type)
        warnings: list[str] = []

        if not problem_type:
            warnings.append("primary problem not resolved from cluster metadata")
        if not buyer_type:
            warnings.append("buyer type not resolved; purchase intent confidence may be lower")
        if cluster.name and cluster.name.lower() in {"product market", "product-market", "market"}:
            warnings.append("generic cluster name provides weak purchase-intent signal")

        priors = self.config.problem_priors.get(problem_type or "generic", self.config.problem_priors["generic"])
        buyer_priors = self.config.buyer_priors.get(buyer_type or "unknown", self.config.buyer_priors["unknown"])

        financial_impact_score = priors.get("financial_impact", 50.0)
        usage_frequency_score = priors.get("usage_frequency", 50.0)
        cost_of_error_score = priors.get("cost_of_error", 50.0)
        urgency_score = priors.get("urgency", 50.0)
        perceived_value_score = priors.get("perceived_value", 50.0)
        commercial_context_score = buyer_priors.get("commercial_context", 50.0)
        workflow_criticality_score = buyer_priors.get("workflow_criticality", 50.0)
        repeatability_score = self._repeatability_score(problem_type, cluster)
        replacement_cost_score = self._replacement_cost_score(problem_type)
        llm_substitutability = self._llm_substitutability(problem_type)
        free_alternative_pressure = self._free_alternative_pressure(problem_type)

        features = PurchaseIntentFeatures(
            financial_impact_score=financial_impact_score,
            usage_frequency_score=usage_frequency_score,
            cost_of_error_score=cost_of_error_score,
            urgency_score=urgency_score,
            perceived_value_score=perceived_value_score,
            commercial_context_score=commercial_context_score,
            workflow_criticality_score=workflow_criticality_score,
            repeatability_score=repeatability_score,
            replacement_cost_score=replacement_cost_score,
            llm_substitutability=llm_substitutability,
            free_alternative_pressure=free_alternative_pressure,
            problem_type=problem_type,
            buyer_type=buyer_type,
            workflow_trigger=workflow_trigger,
            consequences=consequences,
            warnings=warnings,
        )
        return features

    def _resolve_problem_type(self, cluster: ProductCluster) -> str | None:
        text = " ".join([
            cluster.name or "",
            cluster.primary_problem or "",
            *(cluster.keywords or []),
            *(cluster.secondary_problems or []),
        ]).lower()
        if not text:
            return None
        if any(token in text for token in ["pricing", "price", "cost", "budget", "roi", "profit", "commission"]):
            return "pricing"
        if any(token in text for token in ["inventory", "stock", "reorder", "sku"]):
            return "inventory"
        if any(token in text for token in ["planner", "schedule", "calendar", "organize", "ideas"]):
            return "planning"
        if any(token in text for token in ["commission", "payroll", "salary", "sales"]):
            return "commission"
        if any(token in text for token in ["budget", "cash", "finance"]):
            return "budget"
        return "generic"

    def _resolve_buyer_type(self, cluster: ProductCluster) -> str | None:
        text = " ".join([cluster.name or "", cluster.niche or "", *(cluster.keywords or [])]).lower()
        if any(token in text for token in ["bakery", "barber", "contractor", "etsy", "seller", "shop", "freelance", "agency", "business"]):
            return "business"
        if any(token in text for token in ["creator", "influencer", "social", "brand"]):
            return "creator"
        if any(token in text for token in ["hobby", "personal", "family", "home"]):
            return "hobbyist"
        return "unknown"

    def _resolve_workflow_trigger(self, problem_type: str | None, cluster: ProductCluster) -> str | None:
        if problem_type in {"pricing", "costing", "budget", "commission", "inventory"}:
            return "before sending quote"
        if problem_type == "planning":
            return "before planning cycle"
        return "during workflow execution"

    def _resolve_consequences(self, problem_type: str | None) -> list[str]:
        mapping = {
            "pricing": ["financial_loss", "lost_revenue", "margin_squeeze"],
            "costing": ["cost_overrun", "margin_squeeze", "pricing_error"],
            "inventory": ["inventory_loss", "stockout", "wasted_inventory"],
            "commission": ["payroll_error", "sales_loss", "operational_failure"],
            "budget": ["overspend", "cash_flow_issue"],
            "roi": ["poor_investment_decision", "missed_profit"],
            "planning": ["wasted_time", "missed_deadline"],
        }
        if problem_type is None:
            return ["unknown_consequence"]
        return mapping.get(problem_type, ["minor_inconvenience"])

    def _repeatability_score(self, problem_type: str | None, cluster: ProductCluster) -> float:
        base = {
            "pricing": 86.0,
            "costing": 82.0,
            "inventory": 90.0,
            "commission": 84.0,
            "budget": 78.0,
            "roi": 76.0,
            "planning": 58.0,
            "generic": 42.0,
        }
        return base.get(problem_type or "generic", 55.0)

    def _replacement_cost_score(self, problem_type: str | None) -> float:
        base = {
            "pricing": 78.0,
            "costing": 76.0,
            "inventory": 80.0,
            "commission": 74.0,
            "budget": 70.0,
            "roi": 72.0,
            "planning": 45.0,
            "generic": 30.0,
        }
        return base.get(problem_type or "generic", 55.0)

    def _llm_substitutability(self, problem_type: str | None) -> float:
        base = {
            "pricing": 15.0,
            "costing": 18.0,
            "inventory": 12.0,
            "commission": 20.0,
            "budget": 25.0,
            "roi": 22.0,
            "planning": 72.0,
            "generic": 85.0,
        }
        return base.get(problem_type or "generic", 50.0)

    def _free_alternative_pressure(self, problem_type: str | None) -> float:
        base = {
            "pricing": 18.0,
            "costing": 20.0,
            "inventory": 15.0,
            "commission": 10.0,
            "budget": 12.0,
            "roi": 18.0,
            "planning": 60.0,
            "generic": 80.0,
        }
        return base.get(problem_type or "generic", 35.0)
