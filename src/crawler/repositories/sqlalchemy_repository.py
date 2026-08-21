from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, create_engine, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from crawler.clustering import ClusterRun, ProductCluster, ProductClusterMembership
from crawler.models import Marketplace, Product, ProductType, RawMarketplaceProduct
from crawler.repositories.base import ClusterRepository, ProductRepository, RepositoryError, UpsertResult

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class RawProductRecord(Base):
    __tablename__ = "raw_marketplace_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    marketplace: Mapped[str] = mapped_column(String(64), index=True)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    query: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProductRecord(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("identity_key", name="uq_products_identity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identity_key: Mapped[str] = mapped_column(String(2048), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    product_name: Mapped[str] = mapped_column(Text)
    marketplace: Mapped[str] = mapped_column(String(64), index=True)
    niche: Mapped[str | None] = mapped_column(String(255))
    product_type: Mapped[str | None] = mapped_column(String(64))
    price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    currency: Mapped[str | None] = mapped_column(String(3))
    review_count: Mapped[int | None] = mapped_column(Integer)
    rating: Mapped[float | None] = mapped_column(Float)
    seller: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    keywords: Mapped[list[str]] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(Text)
    image_urls: Mapped[list[str]] = mapped_column(JSON)
    category: Mapped[str | None] = mapped_column(Text)
    listing_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    listing_age_days: Mapped[int | None] = mapped_column(Integer)
    query: Mapped[str | None] = mapped_column(Text)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    raw_product_id: Mapped[int | None] = mapped_column(ForeignKey("raw_marketplace_products.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class ClusterRunRecord(Base):
    __tablename__ = "cluster_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    algorithm: Mapped[str] = mapped_column(String(64), index=True)
    algorithm_version: Mapped[str] = mapped_column(String(32), index=True)
    similarity_engine: Mapped[str] = mapped_column(String(64), index=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON)
    product_count: Mapped[int] = mapped_column(Integer)
    cluster_count: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class ProductClusterRecord(Base):
    __tablename__ = "product_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("cluster_runs.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), index=True, unique=True)
    niche: Mapped[str | None] = mapped_column(String(255))
    product_type: Mapped[str | None] = mapped_column(String(64))
    primary_problem: Mapped[str | None] = mapped_column(String(255))
    secondary_problems: Mapped[list[str]] = mapped_column(JSON, default=list)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    product_count: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class ProductClusterMembershipRecord(Base):
    __tablename__ = "product_cluster_memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("product_clusters.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    membership_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class SqlAlchemyProductRepository(ProductRepository, ClusterRepository):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._ensure_sqlite_parent(database_url)
        self.engine = create_engine(database_url)
        self._sessions = sessionmaker(self.engine, expire_on_commit=False)

    @staticmethod
    def _ensure_sqlite_parent(database_url: str) -> None:
        parsed = make_url(database_url)
        if parsed.drivername.startswith("sqlite") and parsed.database not in {None, "", ":memory:"}:
            Path(parsed.database).expanduser().parent.mkdir(parents=True, exist_ok=True)

    def create_schema(self) -> None:
        try:
            Base.metadata.create_all(self.engine)
        except SQLAlchemyError as exc:
            logger.exception("database error while creating schema")
            raise RepositoryError("Não foi possível criar o schema do banco.") from exc

    def save_raw(self, raw: RawMarketplaceProduct) -> RawMarketplaceProduct:
        now = datetime.now(timezone.utc)
        record = RawProductRecord(
            marketplace=raw.marketplace.value,
            external_id=raw.external_id,
            query=raw.query,
            raw_payload=raw.raw_payload,
            collected_at=raw.collected_at,
            created_at=raw.created_at or now,
        )
        try:
            with self._sessions.begin() as session:
                session.add(record)
                session.flush()
                raw.id = record.id
                raw.created_at = _aware(record.created_at)
            logger.debug("raw product collected marketplace=%s raw_id=%s", raw.marketplace, raw.id)
            return raw
        except SQLAlchemyError as exc:
            logger.exception("database error while saving raw marketplace=%s", raw.marketplace)
            raise RepositoryError("Não foi possível persistir a observação raw.") from exc

    def upsert_product(self, product: Product) -> UpsertResult:
        identity_key = _identity_key(product)
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = session.scalar(
                    select(ProductRecord).where(ProductRecord.identity_key == identity_key)
                )
                inserted = record is None
                if record is None:
                    record = ProductRecord(
                        identity_key=identity_key,
                        created_at=product.created_at or now,
                        **_record_values(product),
                    )
                    session.add(record)
                    logger.debug("product inserted identity=%s", identity_key)
                else:
                    for field, value in _record_values(product).items():
                        setattr(record, field, value)
                    logger.debug("product updated identity=%s", identity_key)
                record.updated_at = now
                session.flush()
                saved = _to_product(record)
            return UpsertResult(product=saved, inserted=inserted)
        except SQLAlchemyError as exc:
            logger.exception("database error while upserting product identity=%s", identity_key)
            raise RepositoryError("Não foi possível persistir o produto canônico.") from exc

    def get_by_marketplace_id(
        self, marketplace: Marketplace, external_id: str
    ) -> Product | None:
        return self._one(
            select(ProductRecord).where(
                ProductRecord.marketplace == marketplace.value,
                ProductRecord.external_id == external_id,
            )
        )

    def find(
        self, marketplace: Marketplace | None = None, limit: int = 100
    ) -> list[Product]:
        try:
            with self._sessions() as session:
                statement = select(ProductRecord)
                if marketplace is not None:
                    statement = statement.where(ProductRecord.marketplace == marketplace.value)
                records = session.scalars(statement.order_by(ProductRecord.updated_at.desc()).limit(limit)).all()
                return [_to_product(record) for record in records]
        except SQLAlchemyError as exc:
            logger.exception("database error while listing products")
            raise RepositoryError("Não foi possível consultar os produtos.") from exc

    def find_recent(self, limit: int = 20) -> list[Product]:
        return self.find(limit=limit)

    def find_raw(self, limit: int = 20) -> list[RawMarketplaceProduct]:
        try:
            with self._sessions() as session:
                records = session.scalars(
                    select(RawProductRecord).order_by(RawProductRecord.id.desc()).limit(limit)
                ).all()
                return [_to_raw(record) for record in records]
        except SQLAlchemyError as exc:
            logger.exception("database error while listing raw products")
            raise RepositoryError("Não foi possível consultar observações raw.") from exc

    def count_products(self) -> int:
        return self._count(ProductRecord)

    def count_raw(self) -> int:
        return self._count(RawProductRecord)

    def save_cluster_run(self, run: ClusterRun) -> ClusterRun:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = ClusterRunRecord(
                    algorithm=run.algorithm,
                    algorithm_version=run.algorithm_version,
                    similarity_engine=run.similarity_engine,
                    parameters=run.parameters,
                    product_count=run.product_count,
                    cluster_count=run.cluster_count,
                    started_at=run.started_at or now,
                    completed_at=run.completed_at or now,
                )
                session.add(record)
                session.flush()
                run.id = record.id
            return run
        except SQLAlchemyError as exc:
            logger.exception("database error while saving cluster run")
            raise RepositoryError("Não foi possível persistir o run de clusterização.") from exc

    def save_cluster(self, cluster: ProductCluster) -> ProductCluster:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = ProductClusterRecord(
                    run_id=cluster.run_id,
                    name=cluster.name,
                    slug=cluster.slug,
                    niche=cluster.niche,
                    product_type=cluster.product_type,
                    primary_problem=cluster.primary_problem,
                    secondary_problems=cluster.secondary_problems,
                    keywords=cluster.keywords,
                    product_count=cluster.product_count,
                    confidence=cluster.confidence,
                    created_at=cluster.created_at or now,
                    updated_at=cluster.updated_at or now,
                )
                session.add(record)
                session.flush()
                cluster.id = record.id
            return cluster
        except SQLAlchemyError as exc:
            logger.exception("database error while saving cluster=%s", cluster.name)
            raise RepositoryError("Não foi possível persistir o cluster.") from exc

    def save_membership(self, membership: ProductClusterMembership) -> ProductClusterMembership:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                product = session.scalar(select(ProductRecord).where(ProductRecord.identity_key == _identity_key(membership.product)))
                if product is None:
                    raise RepositoryError("Produto canônico não encontrado para associação de cluster.")
                record = ProductClusterMembershipRecord(
                    cluster_id=membership.cluster_id,
                    product_id=product.id,
                    membership_score=membership.membership_score,
                    created_at=membership.created_at or now,
                )
                session.add(record)
                session.flush()
                membership.id = record.id
            return membership
        except SQLAlchemyError as exc:
            logger.exception("database error while saving cluster membership for product=%s", membership.product.product_name)
            raise RepositoryError("Não foi possível persistir a associação de cluster.") from exc

    def list_clusters(self, limit: int = 20) -> list[ProductCluster]:
        try:
            with self._sessions() as session:
                records = session.scalars(select(ProductClusterRecord).order_by(ProductClusterRecord.product_count.desc(), ProductClusterRecord.created_at.desc()).limit(limit)).all()
                return [_to_cluster(record) for record in records]
        except SQLAlchemyError as exc:
            logger.exception("database error while listing clusters")
            raise RepositoryError("Não foi possível consultar os clusters.") from exc

    def get_cluster_by_id(self, cluster_id: int) -> ProductCluster | None:
        try:
            with self._sessions() as session:
                record = session.get(ProductClusterRecord, cluster_id)
                return _to_cluster(record) if record else None
        except SQLAlchemyError as exc:
            logger.exception("database error while retrieving cluster")
            raise RepositoryError("Não foi possível consultar o cluster.") from exc

    def _one(self, statement: Any) -> Product | None:
        try:
            with self._sessions() as session:
                record = session.scalar(statement)
                return _to_product(record) if record else None
        except SQLAlchemyError as exc:
            logger.exception("database error while retrieving product")
            raise RepositoryError("Não foi possível consultar o produto.") from exc

    def _count(self, model: type[Base]) -> int:
        try:
            with self._sessions() as session:
                return int(session.scalar(select(func.count()).select_from(model)) or 0)
        except SQLAlchemyError as exc:
            logger.exception("database error while counting records")
            raise RepositoryError("Não foi possível contar registros.") from exc


def _identity_key(product: Product) -> str:
    if product.external_id:
        return f"{product.marketplace.value}:id:{product.external_id}"
    if product.url:
        return f"{product.marketplace.value}:url:{product.url}"
    raise RepositoryError("Produto sem external_id e URL canônica não possui identidade.")


def _record_values(product: Product) -> dict[str, Any]:
    return {
        "external_id": product.external_id,
        "product_name": product.product_name,
        "marketplace": product.marketplace.value,
        "niche": product.niche,
        "product_type": product.product_type.value if product.product_type else None,
        "price": product.price,
        "currency": product.currency,
        "review_count": product.review_count,
        "rating": product.rating,
        "seller": product.seller,
        "url": product.url,
        "keywords": product.keywords,
        "description": product.description,
        "image_urls": product.image_urls,
        "category": product.category,
        "listing_date": product.listing_date,
        "listing_age_days": product.listing_age_days,
        "query": product.query,
        "collected_at": product.collected_at,
        "raw_product_id": product.raw_product_id,
    }


def _to_product(record: ProductRecord) -> Product:
    return Product(
        id=record.id,
        external_id=record.external_id,
        product_name=record.product_name,
        marketplace=Marketplace(record.marketplace),
        niche=record.niche,
        product_type=ProductType(record.product_type) if record.product_type else None,
        price=record.price,
        currency=record.currency,
        review_count=record.review_count,
        rating=record.rating,
        seller=record.seller,
        url=record.url,
        keywords=list(record.keywords or []),
        description=record.description,
        image_urls=list(record.image_urls or []),
        category=record.category,
        listing_date=_aware(record.listing_date),
        listing_age_days=record.listing_age_days,
        query=record.query,
        collected_at=_aware(record.collected_at),
        raw_product_id=record.raw_product_id,
        created_at=_aware(record.created_at),
        updated_at=_aware(record.updated_at),
    )


def _to_cluster(record: ProductClusterRecord) -> ProductCluster:
    return ProductCluster(
        id=record.id,
        run_id=record.run_id,
        name=record.name,
        slug=record.slug,
        niche=record.niche,
        product_type=record.product_type,
        primary_problem=record.primary_problem,
        secondary_problems=list(record.secondary_problems or []),
        keywords=list(record.keywords or []),
        product_count=record.product_count,
        confidence=record.confidence,
        created_at=_aware(record.created_at),
        updated_at=_aware(record.updated_at),
    )


def _to_raw(record: RawProductRecord) -> RawMarketplaceProduct:
    return RawMarketplaceProduct(
        id=record.id,
        marketplace=Marketplace(record.marketplace),
        external_id=record.external_id,
        query=record.query,
        raw_payload=dict(record.raw_payload),
        collected_at=_aware(record.collected_at),
        created_at=_aware(record.created_at),
    )


def _aware(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone.utc)
