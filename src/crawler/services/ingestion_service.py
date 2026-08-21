from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from crawler.models import Marketplace, Product, SearchResult
from crawler.normalizers.base import NormalizationError
from crawler.normalizers.registry import ProductNormalizerRegistry
from crawler.providers.base import MarketplaceProvider
from crawler.repositories.base import ProductRepository, RepositoryError

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestionReport:
    query: str
    marketplace: Marketplace
    collected_at: datetime
    raw_collected: int = 0
    normalized: int = 0
    inserted: int = 0
    updated: int = 0
    failed: int = 0
    products: list[Product] = field(default_factory=list)

    def as_search_result(self) -> SearchResult:
        return SearchResult(
            query=self.query,
            marketplace=self.marketplace,
            collected_at=self.collected_at,
            products=self.products,
        )


class ProductIngestionService:
    def __init__(
        self,
        normalizers: ProductNormalizerRegistry,
        repository: ProductRepository | None = None,
    ) -> None:
        self.normalizers = normalizers
        self.repository = repository

    def ingest_search(
        self, provider: MarketplaceProvider, query: str, limit: int = 50
    ) -> IngestionReport:
        query = " ".join(query.split())
        if not query:
            raise ValueError("A query não pode ser vazia.")
        if limit < 1:
            raise ValueError("O limite deve ser maior que zero.")

        raw_products = provider.search(query, limit)
        report = IngestionReport(
            query=query,
            marketplace=provider.marketplace,
            collected_at=datetime.now(timezone.utc),
            raw_collected=len(raw_products),
        )
        canonical_by_identity: dict[str, Product] = {}
        for raw in raw_products:
            try:
                logger.debug(
                    "raw product collected marketplace=%s external_id=%s",
                    raw.marketplace.value,
                    raw.external_id,
                )
                if self.repository is not None:
                    self.repository.save_raw(raw)
                product = self.normalizers.get(raw.marketplace).normalize(raw)
                report.normalized += 1
                logger.debug(
                    "normalization success marketplace=%s external_id=%s",
                    raw.marketplace.value,
                    raw.external_id,
                )
                if self.repository is not None:
                    outcome = self.repository.upsert_product(product)
                    product = outcome.product
                    if outcome.inserted:
                        report.inserted += 1
                    else:
                        report.updated += 1
                identity = _identity(product)
                if identity in canonical_by_identity:
                    logger.debug("duplicate detected identity=%s", identity)
                canonical_by_identity[identity] = product
            except NormalizationError as exc:
                report.failed += 1
                logger.warning(
                    "normalization failure marketplace=%s external_id=%s error=%s",
                    raw.marketplace.value,
                    raw.external_id,
                    exc,
                )
            except RepositoryError:
                report.failed += 1
                logger.exception(
                    "database error marketplace=%s external_id=%s",
                    raw.marketplace.value,
                    raw.external_id,
                )
            except Exception:
                report.failed += 1
                logger.exception(
                    "unexpected normalization failure marketplace=%s external_id=%s",
                    raw.marketplace.value,
                    raw.external_id,
                )
        report.products = list(canonical_by_identity.values())
        return report


def _identity(product: Product) -> str:
    suffix = f"id:{product.external_id}" if product.external_id else f"url:{product.url}"
    return f"{product.marketplace.value}:{suffix}"

