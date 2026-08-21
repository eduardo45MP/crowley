from datetime import datetime, timezone

from crawler.models import Marketplace, RawMarketplaceProduct
from crawler.normalizers.registry import default_normalizer_registry
from crawler.providers.mock import MockMarketplaceProvider
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from crawler.services.ingestion_service import ProductIngestionService
from crawler.services.search_service import SearchService


class PartiallyInvalidMockProvider(MockMarketplaceProvider):
    def search(self, query: str, limit: int) -> list[RawMarketplaceProduct]:
        valid = super().search(query, 1)[0]
        invalid = RawMarketplaceProduct(
            marketplace=Marketplace.MOCK,
            external_id="broken",
            query=query,
            raw_payload={"name": "Missing URL"},
            collected_at=datetime.now(timezone.utc),
        )
        return [valid, invalid]


def _repository() -> SqlAlchemyProductRepository:
    repository = SqlAlchemyProductRepository("sqlite+pysqlite:///:memory:")
    repository.create_schema()
    return repository


def test_ingestion_service_persists_raw_and_canonical_records():
    repository = _repository()
    service = ProductIngestionService(default_normalizer_registry(), repository)

    report = service.ingest_search(MockMarketplaceProvider(), " bakery   calculator ", 3)

    assert report.query == "bakery calculator"
    assert report.marketplace is Marketplace.MOCK
    assert report.raw_collected == 3
    assert report.normalized == 3
    assert report.inserted == 3
    assert report.updated == 0
    assert report.failed == 0
    assert repository.count_raw() == 3
    assert repository.count_products() == 3


def test_repeated_ingestion_creates_history_and_updates_products():
    repository = _repository()
    service = ProductIngestionService(default_normalizer_registry(), repository)

    first = service.ingest_search(MockMarketplaceProvider(), "calculator", 1)
    second = service.ingest_search(MockMarketplaceProvider(), "calculator", 1)

    assert first.inserted == 1
    assert second.updated == 1
    assert repository.count_raw() == 2
    assert repository.count_products() == 1


def test_search_service_compatibility_facade_returns_normalized_products():
    result = SearchService(MockMarketplaceProvider()).search("bakery calculator", 1)

    assert result.products[0].product_name == "Bakery Pricing Calculator"
    assert result.products[0].marketplace is Marketplace.MOCK


def test_structural_failure_keeps_raw_record_and_continues_batch():
    repository = _repository()
    service = ProductIngestionService(default_normalizer_registry(), repository)

    report = service.ingest_search(PartiallyInvalidMockProvider(), "calculator", 2)

    assert report.raw_collected == 2
    assert report.normalized == 1
    assert report.failed == 1
    assert repository.count_raw() == 2
    assert repository.count_products() == 1
    assert len(repository.find(Marketplace.MOCK)) == 1
