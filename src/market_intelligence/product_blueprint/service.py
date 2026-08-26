from __future__ import annotations

from typing import Any

from market_intelligence.deep_research.models import DeepResearchDossier
from market_intelligence.product_blueprint.config import ProductBlueprintConfig, default_product_blueprint_config
from market_intelligence.product_blueprint.feature_planner import plan_features
from market_intelligence.product_blueprint.formula_planner import build_formulas
from market_intelligence.product_blueprint.models import DashboardBlueprint, ProductBlueprint, ProductField, WorkflowBlueprint
from market_intelligence.product_blueprint.positioning import derive_positioning
from market_intelligence.product_blueprint.structure_planner import plan_structure


class ProductBlueprintService:
    def __init__(self, config: ProductBlueprintConfig | None = None) -> None:
        self.config = config or default_product_blueprint_config()

    def _estimate_hours(self, sheet_count: int, feature_count: int) -> float:
        return round(max(4.0, (sheet_count * 1.0) + (feature_count * 0.5)), 2)

    def _blueprint_confidence(self, dossier: DeepResearchDossier, thesis: Any | None = None) -> float:
        base = float(dossier.research_confidence or 0.0)
        if thesis is not None:
            base += float(getattr(thesis, "confidence", 0.0)) * 0.4
        return round(min(1.0, base), 4)

    def create(self, cluster: Any, dossier: DeepResearchDossier, thesis: Any | None = None) -> ProductBlueprint:
        cluster_name = getattr(cluster, "name", None) or getattr(dossier, "cluster_name", None) or "Product"
        primary_problem = getattr(cluster, "primary_problem", None) or "pricing and workflow planning"
        product_type = getattr(cluster, "product_type", None) or "calculator"
        target_buyer = getattr(cluster, "niche", None) or "small business operators"
        feature_plan = plan_features(dossier, thesis)
        core_features = feature_plan["core_features"]
        differentiation_features = feature_plan["differentiation_features"]
        structure = plan_structure(cluster_name, primary_problem)
        formulas = build_formulas(cluster_name, primary_problem, str(product_type))
        positioning = derive_positioning(cluster_name, thesis, dossier)
        inputs = [
            ProductField(name="cost_inputs", description="Core inputs used to calculate the product cost", field_type="number", required=True),
            ProductField(name="target_margin", description="Target margin or markup goal", field_type="number", required=True),
            ProductField(name="waste_rate", description="Expected waste or loss percentage", field_type="number", required=False),
        ]
        outputs = [
            ProductField(name="recommended_price", description="Suggested selling price", field_type="number", required=True),
            ProductField(name="margin", description="Estimated profit margin", field_type="number", required=True),
            ProductField(name="unit_cost", description="Unit cost calculation", field_type="number", required=True),
        ]
        dashboards = [
            DashboardBlueprint(name="Summary", purpose="Current pricing and margin overview", metrics=["average_margin", "unit_cost", "recommended_price"]),
        ]
        workflows = [
            WorkflowBlueprint(step=1, name="Setup", description="Configure pricing assumptions and units", input_dependencies=["cost_inputs"], output="default_configuration"),
            WorkflowBlueprint(step=2, name="Calculate", description="Run core pricing formulas", input_dependencies=["cost_inputs", "target_margin"], output="recommended_price"),
            WorkflowBlueprint(step=3, name="Review", description="Review margin and viability results", input_dependencies=["recommended_price"], output="summary_dashboard"),
        ]
        warnings: list[str] = []
        if (dossier.research_confidence or 0.0) < 0.6:
            warnings.append("Low research confidence; blueprint should be treated as provisional.")
        if len(structure) > self.config.max_sheets:
            warnings.append("Structure exceeds recommended sheet count; scope review required.")
        estimated_hours = self._estimate_hours(len(structure), len(core_features) + len(differentiation_features))
        confidence = self._blueprint_confidence(dossier, thesis)
        return ProductBlueprint(
            cluster_id=getattr(cluster, "id", None) or getattr(dossier, "cluster_id", None),
            product_name=cluster_name,
            product_type=str(product_type),
            target_buyer=str(target_buyer),
            primary_problem=str(primary_problem),
            value_proposition=f"Simplify {primary_problem} and make price decisions more transparent.",
            sheets=structure,
            formulas=formulas,
            inputs=inputs,
            outputs=outputs,
            dashboards=dashboards,
            workflows=workflows,
            core_features=core_features[:6],
            differentiation_features=differentiation_features[:6],
            optional_features=["advanced scenario analysis", "supplier history", "multi-currency support"],
            mvp_features=core_features[:4],
            post_mvp_features=differentiation_features[:3],
            configuration_options=["currency", "units", "target_margin", "tax_handling"],
            documentation_requirements=["quick start", "formula assumptions", "FAQ"],
            scope_level="micro" if len(structure) <= 7 else "small",
            build_complexity="medium" if len(differentiation_features) <= 3 else "high",
            estimated_build_hours=estimated_hours,
            evidence_refs=[
                f"research_confidence={dossier.research_confidence}",
                f"coverage={dossier.research_coverage}",
                *(dossier.market_patterns or [])[:2],
            ],
            blueprint_confidence=confidence,
            warnings=warnings,
            status="ready" if not warnings else "review_required",
            created_at=dossier.created_at,
        )
