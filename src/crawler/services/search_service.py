from __future__ import annotations

from crawler.models import SearchResult
from crawler.normalizers.registry import ProductNormalizerRegistry, default_normalizer_registry
from crawler.providers.base import MarketplaceProvider
from crawler.services.ingestion_service import ProductIngestionService


class SearchService:
    """Compatibility facade for callers that only need normalized search results."""

    def __init__(
        self,
        provider: MarketplaceProvider,
        normalizers: ProductNormalizerRegistry | None = None,
    ) -> None:
        self.provider = provider
        self.normalizers = normalizers or default_normalizer_registry()

    def search(self, query: str, limit: int = 50) -> SearchResult:
        report = ProductIngestionService(self.normalizers).ingest_search(
            self.provider, query, limit
        )
        return report.as_search_result()
