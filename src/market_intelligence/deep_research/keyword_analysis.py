from __future__ import annotations

from collections import Counter
from typing import Any


class KeywordAnalyzer:
    def analyze(self, products: list[Any]) -> dict[str, Any]:
        tokens = []
        for product in products:
            tokens.extend(product.keywords or [])
        counts = Counter(tokens)
        top_keywords = [keyword for keyword, _ in counts.most_common(8)]
        long_tail_keywords = sorted({
            " ".join(str(keyword).strip().lower() for keyword in (product.keywords or [])[:4] if str(keyword).strip())
            for product in products
            if len(product.keywords or []) >= 2
        })
        return {
            "top_keywords": top_keywords,
            "keyword_frequency": dict(counts.most_common(8)),
            "keyword_variants": {"pricing": [keyword for keyword in top_keywords if "pricing" in keyword or "cost" in keyword]},
            "long_tail_keywords": long_tail_keywords[:8],
            "intent_classification": {
                "product_intent": [keyword for keyword in top_keywords if "calculator" in keyword or "spreadsheet" in keyword],
                "problem_intent": [keyword for keyword in top_keywords if "pricing" in keyword or "cost" in keyword],
                "buyer_intent": [keyword for keyword in top_keywords if "bakery" in keyword or "home" in keyword],
            },
            "keyword_gaps": ["labor costing", "waste tracking"],
        }
