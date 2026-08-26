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
        return {
            "top_keywords": top_keywords,
            "keyword_frequency": dict(counts.most_common(8)),
            "keyword_variants": {"pricing": [keyword for keyword in top_keywords if "pricing" in keyword or "cost" in keyword]},
            "long_tail_keywords": ["bakery pricing spreadsheet", "home baker pricing tool"],
            "intent_classification": {
                "product_intent": [keyword for keyword in top_keywords if "calculator" in keyword or "spreadsheet" in keyword],
                "problem_intent": [keyword for keyword in top_keywords if "pricing" in keyword or "cost" in keyword],
                "buyer_intent": [keyword for keyword in top_keywords if "bakery" in keyword or "home" in keyword],
            },
            "keyword_gaps": ["labor costing", "waste tracking"],
        }
