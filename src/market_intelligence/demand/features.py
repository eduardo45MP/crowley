from __future__ import annotations

from collections import Counter

from crawler.clustering import ProductCluster


def _normalize_keyword(keyword: str) -> str:
    return keyword.strip().lower().replace(" ", "-")


class DemandFeaturesExtractor:
    def extract(self, cluster: ProductCluster) -> dict[str, float | list[str] | str | None]:
        keywords = [item.lower() for item in cluster.keywords or []]
        if not keywords:
            keywords = [item.lower() for item in cluster.members[0].keywords] if cluster.members else []

        signal_tokens = []
        for member in cluster.members:
            signal_tokens.extend(member.keywords or [])
            if member.niche:
                signal_tokens.append(member.niche.lower())
            if member.product_type is not None:
                signal_tokens.append(member.product_type.value)
            if member.description:
                signal_tokens.extend(token for token in member.description.lower().split() if len(token) > 3)

        signal_counts = Counter(_normalize_keyword(item) for item in signal_tokens if item)
        ranked = [token for token, _ in signal_counts.most_common(12)]
        signed_keywords = [item for item in sorted(set(keywords + ranked), key=lambda value: (-len(value), value))[:10]]

        review_velocity = 0.0
        if cluster.members:
            review_values = [float(member.review_count or 0) for member in cluster.members]
            review_velocity = sum(review_values) / len(review_values)

        signal_density = 0.0
        if signal_tokens:
            signal_density = min(1.0, len(ranked) / max(1, len(cluster.members) * 2))

        evidence_coverage = min(1.0, (cluster.product_count / max(1, len(cluster.members))) * 0.5 + signal_density * 0.5)
        if cluster.product_count <= 1:
            evidence_coverage *= 0.75

        features = {
            "keywords": signed_keywords,
            "signals": ranked,
            "primary_problem": cluster.primary_problem,
            "product_type": cluster.product_type,
            "niche": cluster.niche,
            "review_velocity": round(review_velocity, 2),
            "cluster_size": cluster.product_count,
            "confidence": cluster.confidence or 0.0,
            "signal_density": round(signal_density, 4),
            "evidence_coverage": round(evidence_coverage, 4),
        }
        return features
