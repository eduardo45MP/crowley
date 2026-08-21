from __future__ import annotations

import argparse
import logging
import sys

from sqlalchemy.engine import make_url

from crawler.clustering import ProductCluster, ProductClusterMembership
from crawler.config import CrawlerConfig, load_dotenv
from crawler.models import Marketplace, Product
from crawler.normalizers.registry import default_normalizer_registry
from crawler.providers import EtsyProvider, MockMarketplaceProvider
from crawler.providers.base import MarketplaceProvider, ProviderError
from crawler.repositories.base import RepositoryError
from crawler.repositories.sqlalchemy_repository import SqlAlchemyProductRepository
from crawler.services.clustering_service import ProductClusteringService
from crawler.services.ingestion_service import ProductIngestionService
from crawler.storage.json_store import JsonResultStore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="crawler", description="Pesquisa produtos em marketplaces")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="coletar, normalizar e persistir produtos")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=50)
    search.add_argument("--output", help="arquivo JSON ou diretório base", default="data/raw")
    search.add_argument("--provider", choices=("mock", "etsy"), default="mock")
    search.add_argument("--no-db", action="store_true", help="não persistir no banco relacional")
    search.add_argument("--verbose", action="store_true")

    products = subparsers.add_parser("products", help="listar produtos canônicos recentes")
    products.add_argument("--limit", type=int, default=20)
    products.add_argument("--verbose", action="store_true")

    cluster = subparsers.add_parser("cluster", help="agrupar produtos canônicos em mercados de produto")
    cluster.add_argument("--limit", type=int, default=500)
    cluster.add_argument("--marketplace", choices=("etsy", "gumroad", "creative_market", "mock"), default=None)
    cluster.add_argument("--threshold", type=float, default=None)
    cluster.add_argument("--minimum-cluster-size", type=int, default=None)
    cluster.add_argument("--verbose", action="store_true")

    clusters = subparsers.add_parser("clusters", help="listar clusters persistidos")
    clusters.add_argument("--limit", type=int, default=20)
    clusters.add_argument("--verbose", action="store_true")

    cluster_show = subparsers.add_parser("cluster-show", help="inspecionar um cluster pelo id")
    cluster_show.add_argument("cluster_id", type=int)
    cluster_show.add_argument("--verbose", action="store_true")
    return parser


def _provider(name: str, config: CrawlerConfig) -> MarketplaceProvider:
    if name == "etsy":
        return EtsyProvider(config)
    return MockMarketplaceProvider()


def _display_price(product: Product) -> str:
    if product.price is None:
        return "-"
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "BRL": "R$ "}
    prefix = symbols.get(product.currency or "", f"{product.currency} " if product.currency else "")
    return f"{prefix}{product.price:.2f}"


def _database_label(database_url: str) -> str:
    parsed = make_url(database_url)
    if parsed.drivername.startswith("sqlite"):
        return parsed.database or ":memory:"
    return parsed.render_as_string(hide_password=True)


def _repository(config: CrawlerConfig) -> SqlAlchemyProductRepository:
    repository = SqlAlchemyProductRepository(config.database_url)
    repository.create_schema()
    return repository


def _run_search(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = None if args.no_db else _repository(config)
    report = ProductIngestionService(
        default_normalizer_registry(), repository
    ).ingest_search(_provider(args.provider, config), args.query, args.limit)
    path = JsonResultStore(args.output).save(report.as_search_result())

    print(f"Marketplace: {report.marketplace.value.title()}")
    print(f"Query: {report.query}\n")
    for index, product in enumerate(report.products, start=1):
        reviews = product.review_count if product.review_count is not None else "-"
        print(
            f"{index}. {product.product_name}\n"
            f"   {_display_price(product)}\n"
            f"   {reviews} reviews\n"
            f"   {product.url}\n"
        )
    print(f"Raw collected: {report.raw_collected}")
    print(f"Normalized: {report.normalized}")
    print(f"Inserted: {report.inserted}")
    print(f"Updated: {report.updated}")
    print(f"Failed: {report.failed}\n")
    print(f"Database:\n{_database_label(config.database_url) if repository else 'disabled'}\n")
    print(f"JSON saved:\n{path}")
    return 0


def _run_products(args: argparse.Namespace, config: CrawlerConfig) -> int:
    if args.limit < 1:
        raise ValueError("O limite deve ser maior que zero.")
    products = _repository(config).find_recent(args.limit)
    print(f"{'ID':<5} {'Marketplace':<16} {'Product':<38} {'Price':<12} Reviews")
    for product in products:
        name = product.product_name[:36]
        reviews = str(product.review_count) if product.review_count is not None else "-"
        print(
            f"{str(product.id or '-'):<5} {product.marketplace.value:<16} "
            f"{name:<38} {_display_price(product):<12} {reviews}"
        )
    return 0


def _run_cluster(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    marketplace = Marketplace(args.marketplace) if args.marketplace else None
    products = repository.find(marketplace=marketplace, limit=args.limit)
    threshold = config.cluster_similarity_threshold if args.threshold is None else args.threshold
    minimum_size = config.minimum_cluster_size if args.minimum_cluster_size is None else args.minimum_cluster_size
    result = ProductClusteringService(
        similarity_threshold=threshold,
        minimum_cluster_size=minimum_size,
        algorithm=config.cluster_algorithm,
        algorithm_version=config.cluster_algorithm_version,
        similarity_engine=config.cluster_similarity_engine,
    ).cluster_products(products)
    saved_run = repository.save_cluster_run(result.run)
    for cluster in result.clusters:
        cluster.run_id = saved_run.id
        saved_cluster = repository.save_cluster(cluster)
        for membership in cluster.memberships:
            membership.cluster_id = saved_cluster.id
            repository.save_membership(membership)
    print(f"Products analyzed: {len(products)}")
    print(f"Clusters created: {len(result.clusters)}")
    print(f"Threshold: {threshold}")
    print(f"Algorithm: {saved_run.algorithm} ({saved_run.algorithm_version})")
    print(f"Similarity engine: {saved_run.similarity_engine}")
    for index, cluster in enumerate(sorted(result.clusters, key=lambda item: (-item.product_count, -float(item.confidence or 0.0), item.name.lower()))[:20], start=1):
        print(f"{index}. {cluster.name} | products={cluster.product_count} | confidence={cluster.confidence or 0.0:.2f}")
    return 0


def _run_clusters(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    clusters = repository.list_clusters(limit=args.limit)
    print(f"{'ID':<5} {'Cluster':<34} {'Products':<8} {'Confidence'}")
    for cluster in clusters:
        confidence = f"{(cluster.confidence or 0.0):.2f}"
        print(f"{str(cluster.id or '-'):<5} {cluster.name[:34]:<34} {str(cluster.product_count):<8} {confidence}")
    return 0


def _run_cluster_show(args: argparse.Namespace, config: CrawlerConfig) -> int:
    repository = _repository(config)
    cluster = repository.get_cluster_by_id(args.cluster_id)
    if cluster is None:
        raise ValueError(f"Cluster {args.cluster_id} não encontrado.")
    print(cluster.name)
    print(f"Niche: {cluster.niche or '-'}")
    print(f"Primary problem: {cluster.primary_problem or '-'}")
    print(f"Product type: {cluster.product_type or '-'}")
    print(f"Products: {cluster.product_count}")
    print(f"Confidence: {cluster.confidence or 0.0:.2f}")
    print(f"Keywords: {', '.join(cluster.keywords) if cluster.keywords else '-'}")
    print("Members:")
    for index, member in enumerate(cluster.members, start=1):
        print(f"{index}. {member.product_name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    load_dotenv()
    config = CrawlerConfig.from_env()
    try:
        if args.command == "products":
            return _run_products(args, config)
        if args.command == "cluster":
            return _run_cluster(args, config)
        if args.command == "clusters":
            return _run_clusters(args, config)
        if args.command == "cluster-show":
            return _run_cluster_show(args, config)
        return _run_search(args, config)
    except (ProviderError, RepositoryError, ValueError, OSError) as exc:
        logging.error("%s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
