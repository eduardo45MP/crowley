from datetime import datetime, timezone
from decimal import Decimal

from crawler.models import Marketplace, Product, RawMarketplaceProduct
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository


def _repository() -> SqlAlchemyProductRepository:
    repository = SqlAlchemyProductRepository("sqlite+pysqlite:///:memory:")
    repository.create_schema()
    return repository


def _raw(reviews: int) -> RawMarketplaceProduct:
    return RawMarketplaceProduct(
        marketplace=Marketplace.MOCK,
        external_id="listing-1",
        query="calculator",
        raw_payload={"name": "Calculator", "reviews": reviews},
        collected_at=datetime.now(timezone.utc),
    )


def _product(raw: RawMarketplaceProduct, reviews: int, price: str) -> Product:
    return Product(
        product_name="Calculator",
        marketplace=Marketplace.MOCK,
        external_id=raw.external_id,
        url="https://example.test/listing/1",
        price=Decimal(price),
        currency="USD",
        review_count=reviews,
        keywords=["calculator"],
        query=raw.query,
        collected_at=raw.collected_at,
        raw_product_id=raw.id,
    )


def test_save_raw_upsert_and_retrieve_product():
    repository = _repository()
    raw = repository.save_raw(_raw(100))
    outcome = repository.upsert_product(_product(raw, 100, "12.99"))
    retrieved = repository.get_by_marketplace_id(Marketplace.MOCK, "listing-1")

    assert raw.id is not None
    assert outcome.inserted is True
    assert retrieved is not None
    assert retrieved.product_name == "Calculator"
    assert retrieved.price == Decimal("12.9900")
    assert retrieved.raw_product_id == raw.id


def test_two_observations_update_one_canonical_product_and_keep_raw_history():
    repository = _repository()
    first_raw = repository.save_raw(_raw(100))
    repository.upsert_product(_product(first_raw, 100, "12.99"))
    second_raw = repository.save_raw(_raw(120))
    outcome = repository.upsert_product(_product(second_raw, 120, "14.99"))

    product = repository.get_by_marketplace_id(Marketplace.MOCK, "listing-1")
    assert outcome.inserted is False
    assert repository.count_raw() == 2
    assert repository.count_products() == 1
    assert product is not None
    assert product.review_count == 120
    assert product.price == Decimal("14.9900")
    assert product.raw_product_id == second_raw.id
    assert [raw.raw_payload["reviews"] for raw in repository.find_raw()] == [120, 100]

