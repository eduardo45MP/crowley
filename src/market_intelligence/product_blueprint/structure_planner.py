from __future__ import annotations

from market_intelligence.product_blueprint.models import SheetBlueprint


def plan_structure(cluster_name: str, primary_problem: str | None) -> list[SheetBlueprint]:
    name = (cluster_name or "").lower()
    if "bakery" in name or "pricing" in (primary_problem or "").lower():
        sheets = [
            SheetBlueprint(name="Settings", purpose="Global configuration for currency, units, tax and margin assumptions.", input_fields=["currency", "tax_rate", "default_margin"], calculated_fields=[], output_fields=["defaults"], dependencies=[], required=True),
            SheetBlueprint(name="Ingredients", purpose="Maintain ingredient list and supplier data.", input_fields=["ingredient", "supplier", "package_size", "package_cost"], calculated_fields=["unit_cost"], output_fields=["ingredient_cost"], dependencies=["Settings"], required=True),
            SheetBlueprint(name="Recipes", purpose="Map ingredients to each product recipe.", input_fields=["recipe", "ingredient", "quantity_used"], calculated_fields=["recipe_cost"], output_fields=["recipe_total"], dependencies=["Ingredients"], required=True),
            SheetBlueprint(name="Packaging", purpose="Assign packaging assumptions and incidental product costs.", input_fields=["packaging_type", "cost_per_unit"], calculated_fields=["packaging_cost"], output_fields=["total_packaging_cost"], dependencies=["Settings"], required=True),
            SheetBlueprint(name="Labor", purpose="Track labor minutes, hourly cost and efficiency.", input_fields=["labor_minutes", "hourly_rate"], calculated_fields=["labor_cost"], output_fields=["total_labor_cost"], dependencies=["Settings"], required=True),
            SheetBlueprint(name="Pricing", purpose="Compute suggested price and margin.", input_fields=["target_margin", "product_cost"], calculated_fields=["suggested_price", "margin"], output_fields=["recommended_price"], dependencies=["Recipes", "Packaging", "Labor"], required=True),
            SheetBlueprint(name="Dashboard", purpose="High-level profitability and pricing overview.", input_fields=[], calculated_fields=["average_margin", "top_products"], output_fields=["summary_metrics"], dependencies=["Pricing"], required=True),
        ]
        return sheets
    return [
        SheetBlueprint(name="Settings", purpose="Configure operating assumptions.", input_fields=["currency", "units", "default_margin"], calculated_fields=[], output_fields=["defaults"], dependencies=[], required=True),
        SheetBlueprint(name="Inputs", purpose="Collect important product and business inputs.", input_fields=["item", "quantity", "cost"], calculated_fields=["input_total"], output_fields=["baseline_cost"], dependencies=["Settings"], required=True),
        SheetBlueprint(name="Calculations", purpose="Create the core formulas that solve the problem.", input_fields=["input_total", "assumptions"], calculated_fields=["unit_cost", "total_cost"], output_fields=["calculated_cost"], dependencies=["Inputs"], required=True),
        SheetBlueprint(name="Pricing", purpose="Translate cost into pricing and profit decisions.", input_fields=["target_margin"], calculated_fields=["suggested_price", "margin"], output_fields=["recommended_price"], dependencies=["Calculations"], required=True),
        SheetBlueprint(name="Dashboard", purpose="Summarize outcomes and monitor performance.", input_fields=[], calculated_fields=["summary_metrics"], output_fields=["summary"], dependencies=["Pricing"], required=True),
    ]
