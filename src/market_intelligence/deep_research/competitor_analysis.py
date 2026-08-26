from __future__ import annotations

from collections import Counter
from typing import Any

from crawler.clustering import ProductCluster


class CompetitorBenchmarkSelector:
    def select(self, cluster: ProductCluster, leader_count: int = 5, mid_market_count: int = 5, emerging_count: int = 5) -> list[Any]:
        members = sorted(list(cluster.members or []), key=lambda item: (-(item.review_count or 0), -(item.rating or 0.0), item.product_name or ""))
        if not members:
            return []
        leaders = members[:leader_count]
        mids = members[min(len(members), leader_count): min(len(members), leader_count + mid_market_count)]
        emerging = members[min(len(members), leader_count + mid_market_count): min(len(members), leader_count + mid_market_count + emerging_count)]
        return list(dict.fromkeys([*leaders, *mids, *emerging]))
