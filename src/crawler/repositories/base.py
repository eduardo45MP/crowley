from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from crawler.clustering import ClusterRun, ProductCluster, ProductClusterMembership
from crawler.models import Marketplace, Product, RawMarketplaceProduct


class RepositoryError(RuntimeError):
    """Persistence operation failed."""


@dataclass(frozen=True, slots=True)
class UpsertResult:
    product: Product
    inserted: bool


class ClusterRepository(ABC):
    @abstractmethod
    def save_cluster_run(self, run: ClusterRun) -> ClusterRun:
        raise NotImplementedError

    @abstractmethod
    def save_cluster(self, cluster: ProductCluster) -> ProductCluster:
        raise NotImplementedError

    @abstractmethod
    def save_membership(self, membership: ProductClusterMembership) -> ProductClusterMembership:
        raise NotImplementedError

    @abstractmethod
    def list_clusters(self, limit: int = 20) -> list[ProductCluster]:
        raise NotImplementedError


class ProductRepository(ABC):
    @abstractmethod
    def create_schema(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_raw(self, raw: RawMarketplaceProduct) -> RawMarketplaceProduct:
        raise NotImplementedError

    @abstractmethod
    def upsert_product(self, product: Product) -> UpsertResult:
        raise NotImplementedError

    @abstractmethod
    def get_by_marketplace_id(
        self, marketplace: Marketplace, external_id: str
    ) -> Product | None:
        raise NotImplementedError

    @abstractmethod
    def find(
        self, marketplace: Marketplace | None = None, limit: int = 100
    ) -> list[Product]:
        raise NotImplementedError

    @abstractmethod
    def find_recent(self, limit: int = 20) -> list[Product]:
        raise NotImplementedError

    @abstractmethod
    def find_raw(self, limit: int = 20) -> list[RawMarketplaceProduct]:
        raise NotImplementedError

    @abstractmethod
    def count_products(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def count_raw(self) -> int:
        raise NotImplementedError
