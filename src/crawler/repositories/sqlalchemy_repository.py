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


class DemandAnalysisRunRecord(Base):
    __tablename__ = "demand_analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON)
    cluster_count: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class ClusterDemandScoreRecord(Base):
    __tablename__ = "cluster_demand_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("demand_analysis_runs.id"), index=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("product_clusters.id"), index=True)
    demand_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    evidence_coverage: Mapped[float] = mapped_column(Float)
    features: Mapped[dict[str, Any]] = mapped_column(JSON)
    components: Mapped[dict[str, Any]] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class CompetitionAnalysisRunRecord(Base):
    __tablename__ = "competition_analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON)
    cluster_count: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class ClusterCompetitionScoreRecord(Base):
    __tablename__ = "cluster_competition_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("competition_analysis_runs.id"), index=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("product_clusters.id"), index=True)
    competition_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    evidence_coverage: Mapped[float] = mapped_column(Float)
    features: Mapped[dict[str, Any]] = mapped_column(JSON)
    components: Mapped[dict[str, Any]] = mapped_column(JSON)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class PurchaseIntentAnalysisRunRecord(Base):
    __tablename__ = "purchase_intent_analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON)
    cluster_count: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class ClusterPurchaseIntentScoreRecord(Base):
    __tablename__ = "cluster_purchase_intent_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("purchase_intent_analysis_runs.id"), index=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("product_clusters.id"), index=True)
    purchase_intent_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    evidence_coverage: Mapped[float] = mapped_column(Float)
    features: Mapped[dict[str, Any]] = mapped_column(JSON)
    components: Mapped[dict[str, Any]] = mapped_column(JSON)
    penalties: Mapped[dict[str, Any]] = mapped_column(JSON)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class BuildEaseAnalysisRunRecord(Base):
    __tablename__ = "build_ease_analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON)
    cluster_count: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class ClusterBuildEaseScoreRecord(Base):
    __tablename__ = "cluster_build_ease_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("build_ease_analysis_runs.id"), index=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("product_clusters.id"), index=True)
    build_ease_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    evidence_coverage: Mapped[float] = mapped_column(Float)
    features: Mapped[dict[str, Any]] = mapped_column(JSON)
    components: Mapped[dict[str, Any]] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class DifferentiationAnalysisRunRecord(Base):
    __tablename__ = "differentiation_analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON)
    cluster_count: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class ClusterDifferentiationScoreRecord(Base):
    __tablename__ = "cluster_differentiation_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("differentiation_analysis_runs.id"), index=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("product_clusters.id"), index=True)
    differentiation_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    evidence_coverage: Mapped[float] = mapped_column(Float)
    features: Mapped[dict[str, Any]] = mapped_column(JSON)
    components: Mapped[dict[str, Any]] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class EligibilityEvaluationRunRecord(Base):
    __tablename__ = "eligibility_evaluation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON)
    cluster_count: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class ClusterEligibilityResultRecord(Base):
    __tablename__ = "cluster_eligibility_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("eligibility_evaluation_runs.id"), index=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("product_clusters.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    ranking_eligible: Mapped[bool] = mapped_column(Integer, default=0)
    triggered_rules: Mapped[list[str]] = mapped_column(JSON, default=list)
    blocking_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    review_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_analysis_ids: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    model_version: Mapped[str] = mapped_column(String(64), index=True)


class OpportunityAnalysisRunRecord(Base):
    __tablename__ = "opportunity_analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    weights: Mapped[dict[str, Any]] = mapped_column(JSON)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON)
    cluster_count: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class ClusterOpportunityScoreRecord(Base):
    __tablename__ = "cluster_opportunity_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("opportunity_analysis_runs.id"), index=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("product_clusters.id"), index=True)
    opportunity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    qualification: Mapped[str | None] = mapped_column(String(32), index=True)
    opportunity_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    dimension_coverage: Mapped[float] = mapped_column(Float)
    evidence_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    ranking_eligible: Mapped[bool] = mapped_column(Integer, default=0)
    components: Mapped[dict[str, Any]] = mapped_column(JSON)
    source_analysis_ids: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    source_model_versions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    bottlenecks: Mapped[list[str]] = mapped_column(JSON, default=list)
    strongest_dimension: Mapped[str | None] = mapped_column(String(64), index=True)
    weakest_dimension: Mapped[str | None] = mapped_column(String(64), index=True)
    fatal_weaknesses: Mapped[list[str]] = mapped_column(JSON, default=list)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class SelectionRunRecord(Base):
    __tablename__ = "selection_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON)
    candidate_count: Mapped[int] = mapped_column(Integer)
    eligible_count: Mapped[int] = mapped_column(Integer)
    selected_count: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class SelectedOpportunityRecord(Base):
    __tablename__ = "selected_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("selection_runs.id"), index=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("product_clusters.id"), index=True)
    cluster_name: Mapped[str | None] = mapped_column(String(255), index=True)
    buyer_group: Mapped[str | None] = mapped_column(String(64), index=True)
    quota_bucket: Mapped[str | None] = mapped_column(String(64), index=True)
    niche: Mapped[str | None] = mapped_column(String(255))
    problem_type: Mapped[str | None] = mapped_column(String(255))
    product_type: Mapped[str | None] = mapped_column(String(64))
    opportunity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    opportunity_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    selection_rank: Mapped[int] = mapped_column(Integer)
    selection_utility: Mapped[float | None] = mapped_column(Float, nullable=True)
    selection_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    selected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


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

    def list_cluster_members(self, cluster_id: int) -> list[Product]:
        try:
            with self._sessions() as session:
                membership_ids = session.scalars(
                    select(ProductClusterMembershipRecord.product_id).where(
                        ProductClusterMembershipRecord.cluster_id == cluster_id
                    )
                ).all()
                if not membership_ids:
                    return []
                records = session.scalars(
                    select(ProductRecord).where(ProductRecord.id.in_(membership_ids))
                ).all()
                return [_to_product(record) for record in records]
        except SQLAlchemyError as exc:
            logger.exception("database error while loading cluster members cluster_id=%s", cluster_id)
            raise RepositoryError("Não foi possível consultar os membros do cluster.") from exc

    def save_demand_run(self, run: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = DemandAnalysisRunRecord(
                    model_version=run.model_version,
                    configuration=run.configuration,
                    cluster_count=run.cluster_count,
                    started_at=run.started_at or now,
                    completed_at=run.completed_at or now,
                )
                session.add(record)
                session.flush()
                run.id = record.id
            return run
        except SQLAlchemyError as exc:
            logger.exception("database error while saving demand run")
            raise RepositoryError("Não foi possível persistir a execução de demanda.") from exc

    def save_cluster_demand_score(self, score: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = ClusterDemandScoreRecord(
                    run_id=score.run_id,
                    cluster_id=score.cluster_id,
                    demand_score=score.demand_score,
                    confidence=score.confidence,
                    evidence_coverage=score.evidence_coverage,
                    features=score.features,
                    components=score.components,
                    model_version=score.model_version,
                    calculated_at=score.calculated_at or now,
                )
                session.add(record)
                session.flush()
                score.id = record.id
            return score
        except SQLAlchemyError as exc:
            logger.exception("database error while saving cluster demand score cluster_id=%s", score.cluster_id)
            raise RepositoryError("Não foi possível persistir o score de demanda.") from exc

    def latest_cluster_demand_score(self, cluster_id: int) -> Any | None:
        try:
            with self._sessions() as session:
                record = session.scalar(
                    select(ClusterDemandScoreRecord)
                    .where(ClusterDemandScoreRecord.cluster_id == cluster_id)
                    .order_by(ClusterDemandScoreRecord.calculated_at.desc())
                )
                if record is None:
                    return None
                return {
                    "id": record.id,
                    "run_id": record.run_id,
                    "cluster_id": record.cluster_id,
                    "demand_score": record.demand_score,
                    "confidence": record.confidence,
                    "evidence_coverage": record.evidence_coverage,
                    "features": record.features,
                    "components": record.components,
                    "model_version": record.model_version,
                    "calculated_at": _aware(record.calculated_at),
                }
        except SQLAlchemyError as exc:
            logger.exception("database error while loading latest demand score cluster_id=%s", cluster_id)
            raise RepositoryError("Não foi possível consultar o score de demanda.") from exc

    def save_competition_run(self, run: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = CompetitionAnalysisRunRecord(
                    model_version=run.model_version,
                    configuration=run.configuration,
                    cluster_count=run.cluster_count,
                    started_at=run.started_at or now,
                    completed_at=run.completed_at or now,
                )
                session.add(record)
                session.flush()
                run.id = record.id
            return run
        except SQLAlchemyError as exc:
            logger.exception("database error while saving competition run")
            raise RepositoryError("Não foi possível persistir a execução de competição.") from exc

    def save_cluster_competition_score(self, score: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = ClusterCompetitionScoreRecord(
                    run_id=score.run_id,
                    cluster_id=score.cluster_id,
                    competition_score=score.competition_score,
                    confidence=score.confidence,
                    evidence_coverage=score.evidence_coverage,
                    features=score.features,
                    components=score.components,
                    warnings=score.warnings,
                    model_version=score.model_version,
                    calculated_at=score.calculated_at or now,
                )
                session.add(record)
                session.flush()
                score.id = record.id
            return score
        except SQLAlchemyError as exc:
            logger.exception("database error while saving competition score cluster_id=%s", score.cluster_id)
            raise RepositoryError("Não foi possível persistir o score de competição.") from exc

    def latest_cluster_competition_score(self, cluster_id: int) -> Any | None:
        try:
            with self._sessions() as session:
                record = session.scalar(
                    select(ClusterCompetitionScoreRecord)
                    .where(ClusterCompetitionScoreRecord.cluster_id == cluster_id)
                    .order_by(ClusterCompetitionScoreRecord.calculated_at.desc())
                )
                if record is None:
                    return None
                return {
                    "id": record.id,
                    "run_id": record.run_id,
                    "cluster_id": record.cluster_id,
                    "competition_score": record.competition_score,
                    "confidence": record.confidence,
                    "evidence_coverage": record.evidence_coverage,
                    "features": record.features,
                    "components": record.components,
                    "warnings": record.warnings,
                    "model_version": record.model_version,
                    "calculated_at": _aware(record.calculated_at),
                }
        except SQLAlchemyError as exc:
            logger.exception("database error while loading latest competition score cluster_id=%s", cluster_id)
            raise RepositoryError("Não foi possível consultar o score de competição.") from exc

    def save_purchase_intent_run(self, run: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = PurchaseIntentAnalysisRunRecord(
                    model_version=run.model_version,
                    configuration=run.configuration,
                    cluster_count=run.cluster_count,
                    started_at=run.started_at or now,
                    completed_at=run.completed_at or now,
                )
                session.add(record)
                session.flush()
                run.id = record.id
            return run
        except SQLAlchemyError as exc:
            logger.exception("database error while saving purchase-intent run")
            raise RepositoryError("Não foi possível persistir a execução de intenção de compra.") from exc

    def save_cluster_purchase_intent_score(self, score: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = ClusterPurchaseIntentScoreRecord(
                    run_id=score.run_id,
                    cluster_id=score.cluster_id,
                    purchase_intent_score=score.purchase_intent_score,
                    confidence=score.confidence,
                    evidence_coverage=score.evidence_coverage,
                    features=score.features,
                    components=score.components,
                    penalties=score.penalties,
                    warnings=score.warnings,
                    model_version=score.model_version,
                    calculated_at=score.calculated_at or now,
                )
                session.add(record)
                session.flush()
                score.id = record.id
            return score
        except SQLAlchemyError as exc:
            logger.exception("database error while saving purchase-intent score cluster_id=%s", score.cluster_id)
            raise RepositoryError("Não foi possível persistir o score de intenção de compra.") from exc

    def latest_cluster_purchase_intent_score(self, cluster_id: int) -> Any | None:
        try:
            with self._sessions() as session:
                record = session.scalar(
                    select(ClusterPurchaseIntentScoreRecord)
                    .where(ClusterPurchaseIntentScoreRecord.cluster_id == cluster_id)
                    .order_by(ClusterPurchaseIntentScoreRecord.calculated_at.desc())
                )
                if record is None:
                    return None
                return {
                    "id": record.id,
                    "run_id": record.run_id,
                    "cluster_id": record.cluster_id,
                    "purchase_intent_score": record.purchase_intent_score,
                    "confidence": record.confidence,
                    "evidence_coverage": record.evidence_coverage,
                    "features": record.features,
                    "components": record.components,
                    "penalties": record.penalties,
                    "warnings": record.warnings,
                    "model_version": record.model_version,
                    "calculated_at": _aware(record.calculated_at),
                }
        except SQLAlchemyError as exc:
            logger.exception("database error while loading latest purchase-intent score cluster_id=%s", cluster_id)
            raise RepositoryError("Não foi possível consultar o score de intenção de compra.") from exc

    def save_build_ease_run(self, run: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = BuildEaseAnalysisRunRecord(
                    model_version=run.model_version,
                    configuration=run.configuration,
                    cluster_count=run.cluster_count,
                    started_at=run.started_at or now,
                    completed_at=run.completed_at or now,
                )
                session.add(record)
                session.flush()
                run.id = record.id
            return run
        except SQLAlchemyError as exc:
            logger.exception("database error while saving build-ease run")
            raise RepositoryError("Não foi possível persistir a execução de build ease.") from exc

    def save_cluster_build_ease_score(self, score: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = ClusterBuildEaseScoreRecord(
                    run_id=score.run_id,
                    cluster_id=score.cluster_id,
                    build_ease_score=score.build_ease_score,
                    confidence=score.confidence,
                    evidence_coverage=score.evidence_coverage,
                    features=score.features,
                    components=score.components,
                    model_version=score.model_version,
                    calculated_at=score.calculated_at or now,
                )
                session.add(record)
                session.flush()
                score.id = record.id
            return score
        except SQLAlchemyError as exc:
            logger.exception("database error while saving build-ease score cluster_id=%s", score.cluster_id)
            raise RepositoryError("Não foi possível persistir o score de facilidade de produção.") from exc

    def latest_cluster_build_ease_score(self, cluster_id: int) -> Any | None:
        try:
            with self._sessions() as session:
                record = session.scalar(
                    select(ClusterBuildEaseScoreRecord)
                    .where(ClusterBuildEaseScoreRecord.cluster_id == cluster_id)
                    .order_by(ClusterBuildEaseScoreRecord.calculated_at.desc())
                )
                if record is None:
                    return None
                return {
                    "id": record.id,
                    "run_id": record.run_id,
                    "cluster_id": record.cluster_id,
                    "build_ease_score": record.build_ease_score,
                    "confidence": record.confidence,
                    "evidence_coverage": record.evidence_coverage,
                    "features": record.features,
                    "components": record.components,
                    "model_version": record.model_version,
                    "calculated_at": _aware(record.calculated_at),
                }
        except SQLAlchemyError as exc:
            logger.exception("database error while loading latest build-ease score cluster_id=%s", cluster_id)
            raise RepositoryError("Não foi possível consultar o score de facilidade de produção.") from exc

    def save_eligibility_run(self, run: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = EligibilityEvaluationRunRecord(
                    model_version=run.model_version,
                    configuration=run.configuration,
                    cluster_count=run.cluster_count,
                    started_at=run.started_at or now,
                    completed_at=run.completed_at or now,
                )
                session.add(record)
                session.flush()
                run.id = record.id
            return run
        except SQLAlchemyError as exc:
            logger.exception("database error while saving eligibility run")
            raise RepositoryError("Não foi possível persistir a execução de eligibility.") from exc

    def latest_cluster_eligibility_result(self, cluster_id: int) -> Any | None:
        try:
            with self._sessions() as session:
                record = session.scalar(
                    select(ClusterEligibilityResultRecord)
                    .where(ClusterEligibilityResultRecord.cluster_id == cluster_id)
                    .order_by(ClusterEligibilityResultRecord.evaluated_at.desc())
                )
                if record is None:
                    return None
                return {
                    "id": record.id,
                    "run_id": record.run_id,
                    "cluster_id": record.cluster_id,
                    "status": record.status,
                    "ranking_eligible": bool(record.ranking_eligible),
                    "triggered_rules": record.triggered_rules,
                    "blocking_reasons": record.blocking_reasons,
                    "review_reasons": record.review_reasons,
                    "warnings": record.warnings,
                    "source_analysis_ids": getattr(record, "source_analysis_ids", {}),
                    "evaluated_at": _aware(record.evaluated_at),
                    "model_version": record.model_version,
                }
        except SQLAlchemyError as exc:
            logger.exception("database error while loading latest eligibility result cluster_id=%s", cluster_id)
            raise RepositoryError("Não foi possível consultar o resultado de eligibility.") from exc

    def save_cluster_eligibility_result(self, result: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = ClusterEligibilityResultRecord(
                    run_id=result.run_id,
                    cluster_id=result.cluster_id,
                    status=result.status,
                    ranking_eligible=1 if result.ranking_eligible else 0,
                    triggered_rules=[rule.rule_id for rule in result.triggered_rules],
                    blocking_reasons=result.blocking_reasons,
                    review_reasons=result.review_reasons,
                    warnings=result.warnings,
                    source_analysis_ids=result.source_analysis_ids if hasattr(result, "source_analysis_ids") else {},
                    evaluated_at=result.evaluated_at or now,
                    model_version=result.model_version,
                )
                session.add(record)
                session.flush()
                result.id = record.id
            return result
        except SQLAlchemyError as exc:
            logger.exception("database error while saving eligibility result cluster_id=%s", result.cluster_id)
            raise RepositoryError("Não foi possível persistir o resultado de eligibility.") from exc

    def save_opportunity_run(self, run: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = OpportunityAnalysisRunRecord(
                    model_version=run.model_version,
                    weights=run.weights,
                    configuration=run.configuration,
                    cluster_count=run.cluster_count,
                    started_at=run.started_at or now,
                    completed_at=run.completed_at or now,
                )
                session.add(record)
                session.flush()
                run.id = record.id
            return run
        except SQLAlchemyError as exc:
            logger.exception("database error while saving opportunity run")
            raise RepositoryError("Não foi possível persistir a execução de opportunity.") from exc

    def save_cluster_opportunity_score(self, score: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = ClusterOpportunityScoreRecord(
                    run_id=score.run_id,
                    cluster_id=score.cluster_id,
                    opportunity_score=score.opportunity_score,
                    status=score.status,
                    qualification=score.qualification,
                    opportunity_confidence=score.opportunity_confidence,
                    dimension_coverage=score.dimension_coverage,
                    evidence_coverage=score.evidence_coverage,
                    ranking_eligible=1 if score.ranking_eligible else 0,
                    components=score.components,
                    source_analysis_ids=score.source_analysis_ids,
                    source_model_versions=score.source_model_versions,
                    bottlenecks=score.bottlenecks,
                    strongest_dimension=score.strongest_dimension,
                    weakest_dimension=score.weakest_dimension,
                    fatal_weaknesses=score.fatal_weaknesses,
                    warnings=score.warnings,
                    model_version=score.model_version,
                    calculated_at=score.calculated_at or now,
                )
                session.add(record)
                session.flush()
                score.id = record.id
            return score
        except SQLAlchemyError as exc:
            logger.exception("database error while saving opportunity score cluster_id=%s", score.cluster_id)
            raise RepositoryError("Não foi possível persistir o score de opportunity.") from exc

    def latest_cluster_opportunity_score(self, cluster_id: int) -> Any | None:
        try:
            with self._sessions() as session:
                record = session.scalar(
                    select(ClusterOpportunityScoreRecord)
                    .where(ClusterOpportunityScoreRecord.cluster_id == cluster_id)
                    .order_by(ClusterOpportunityScoreRecord.calculated_at.desc())
                )
                if record is None:
                    return None
                return {
                    "id": record.id,
                    "run_id": record.run_id,
                    "cluster_id": record.cluster_id,
                    "opportunity_score": record.opportunity_score,
                    "status": record.status,
                    "qualification": record.qualification,
                    "opportunity_confidence": record.opportunity_confidence,
                    "dimension_coverage": record.dimension_coverage,
                    "evidence_coverage": record.evidence_coverage,
                    "ranking_eligible": bool(record.ranking_eligible),
                    "components": record.components,
                    "source_analysis_ids": record.source_analysis_ids,
                    "source_model_versions": record.source_model_versions,
                    "bottlenecks": record.bottlenecks,
                    "strongest_dimension": record.strongest_dimension,
                    "weakest_dimension": record.weakest_dimension,
                    "fatal_weaknesses": record.fatal_weaknesses,
                    "warnings": record.warnings,
                    "model_version": record.model_version,
                    "calculated_at": _aware(record.calculated_at),
                }
        except SQLAlchemyError as exc:
            logger.exception("database error while loading latest opportunity score cluster_id=%s", cluster_id)
            raise RepositoryError("Não foi possível consultar o score de opportunity.") from exc

    def save_differentiation_run(self, run: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = DifferentiationAnalysisRunRecord(
                    model_version=run.model_version,
                    configuration=run.configuration,
                    cluster_count=run.cluster_count,
                    started_at=run.started_at or now,
                    completed_at=run.completed_at or now,
                )
                session.add(record)
                session.flush()
                run.id = record.id
            return run
        except SQLAlchemyError as exc:
            logger.exception("database error while saving differentiation run")
            raise RepositoryError("Não foi possível persistir a execução de diferenciação.") from exc

    def save_cluster_differentiation_score(self, score: Any) -> Any:
        now = datetime.now(timezone.utc)
        try:
            with self._sessions.begin() as session:
                record = ClusterDifferentiationScoreRecord(
                    run_id=score.run_id,
                    cluster_id=score.cluster_id,
                    differentiation_score=score.differentiation_score,
                    confidence=score.confidence,
                    evidence_coverage=score.evidence_coverage,
                    features=score.features,
                    components=score.components,
                    model_version=score.model_version,
                    calculated_at=score.calculated_at or now,
                )
                session.add(record)
                session.flush()
                score.id = record.id
            return score
        except SQLAlchemyError as exc:
            logger.exception("database error while saving differentiation score cluster_id=%s", score.cluster_id)
            raise RepositoryError("Não foi possível persistir o score de diferenciação.") from exc

    def latest_cluster_differentiation_score(self, cluster_id: int) -> Any | None:
        try:
            with self._sessions() as session:
                record = session.scalar(
                    select(ClusterDifferentiationScoreRecord)
                    .where(ClusterDifferentiationScoreRecord.cluster_id == cluster_id)
                    .order_by(ClusterDifferentiationScoreRecord.calculated_at.desc())
                )
                if record is None:
                    return None
                return {
                    "id": record.id,
                    "run_id": record.run_id,
                    "cluster_id": record.cluster_id,
                    "differentiation_score": record.differentiation_score,
                    "confidence": record.confidence,
                    "evidence_coverage": record.evidence_coverage,
                    "features": record.features,
                    "components": record.components,
                    "model_version": record.model_version,
                    "calculated_at": _aware(record.calculated_at),
                }
        except SQLAlchemyError as exc:
            logger.exception("database error while loading latest differentiation score cluster_id=%s", cluster_id)
            raise RepositoryError("Não foi possível consultar o score de diferenciação.") from exc

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
