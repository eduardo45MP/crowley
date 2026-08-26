from __future__ import annotations

from market_intelligence.product_blueprint.models import FormulaBlueprint


def build_formulas(cluster_name: str, primary_problem: str | None, product_type: str | None) -> list[FormulaBlueprint]:
    base_formulas = [
        FormulaBlueprint(
            name="unit_cost",
            purpose="Compute the per-unit cost for a product or recipe.",
            inputs=["package_cost", "quantity", "waste_rate"],
            output="unit_cost",
            formula_description="Unit cost = (package cost / total units) × (1 + waste rate)",
            complexity="low",
            assumptions=["assumes standardized unit measures"],
        ),
        FormulaBlueprint(
            name="recipe_cost",
            purpose="Total ingredient cost before labor and overhead.",
            inputs=["ingredient_costs", "yield", "spoilage_rate"],
            output="recipe_cost",
            formula_description="Recipe cost = sum ingredient cost + waste allowance",
            complexity="medium",
            assumptions=["waste assumptions are explicit"],
        ),
        FormulaBlueprint(
            name="margin",
            purpose="Calculate profit margin from price and cost.",
            inputs=["price", "total_cost"],
            output="margin",
            formula_description="Margin = (price - cost) / price",
            complexity="low",
            assumptions=["margin is measured as percentage of selling price"],
        ),
        FormulaBlueprint(
            name="markup",
            purpose="Calculate markup for pricing decisions.",
            inputs=["price", "total_cost"],
            output="markup",
            formula_description="Markup = (price - cost) / cost",
            complexity="low",
            assumptions=["markup is measured as percentage of cost"],
        ),
    ]
    if "bakery" in (cluster_name or "").lower() or "pricing" in (primary_problem or "").lower() or (product_type or "").lower() == "calculator":
        base_formulas.insert(1, FormulaBlueprint(
            name="labor_cost",
            purpose="Allocate labor time and hourly rate to each item.",
            inputs=["labor_minutes", "hourly_rate"],
            output="labor_cost",
            formula_description="Labor cost = labor minutes / 60 × hourly rate",
            complexity="medium",
            assumptions=["labor time is logged per product"],
        ))
    return base_formulas
