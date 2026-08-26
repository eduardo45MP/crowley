from __future__ import annotations

from typing import Any


class ProductStructureAnalyzer:
    def analyze(self, products: list[Any]) -> dict[str, Any]:
        product = products[0] if products else None
        if product is None:
            return {"sheet_count": None, "sheet_names": [], "input_sections": [], "calculation_sections": [], "output_sections": [], "dashboards": [], "workflows": [], "automation_features": [], "source": None, "confidence": 0.0}
        text = " ".join([product.product_name or "", *(product.keywords or []), product.description or ""]).lower()
        return {
            "sheet_count": len(products),
            "sheet_names": [item.product_name for item in products[:3]],
            "input_sections": ["pricing assumptions", "inventory"] if "pricing" in text or "inventory" in text else ["pricing assumptions"],
            "calculation_sections": ["costing", "margin"] if "cost" in text or "margin" in text else ["costing"],
            "output_sections": ["summary dashboard", "report"] if "dashboard" in text or "report" in text else ["summary"],
            "dashboards": ["summary"] if "dashboard" in text else [],
            "workflows": ["manual pricing review"] if "pricing" in text else [],
            "automation_features": ["formula logic"] if "calculator" in text or "spreadsheet" in text else [],
            "source": product.url,
            "confidence": 0.68,
        }
