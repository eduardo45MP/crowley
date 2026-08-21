from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from crawler.clustering import ClusterRun, ClusterRunResult, ProductCluster, cluster_products
from crawler.models import Product


@dataclass(slots=True)
class ProductClusteringService:
    similarity_threshold: float = 0.72
    minimum_cluster_size: int = 2
    algorithm: str = "connected_components"
    algorithm_version: str = "v1"
    similarity_engine: str = "tfidf"

    def cluster_products(self, products: list[Product]) -> ClusterRunResult:
        started_at = datetime.now(timezone.utc)
        clusters = cluster_products(
            products,
            similarity_threshold=self.similarity_threshold,
            minimum_cluster_size=self.minimum_cluster_size,
        )
        run = ClusterRun(
            algorithm=self.algorithm,
            algorithm_version=self.algorithm_version,
            similarity_engine=self.similarity_engine,
            parameters={
                "similarity_threshold": self.similarity_threshold,
                "minimum_cluster_size": self.minimum_cluster_size,
            },
            product_count=len(products),
            cluster_count=len(clusters),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )
        return ClusterRunResult(run=run, clusters=clusters)
