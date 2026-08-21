from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: Path = Path(".env")) -> None:
    """Load a small, dependency-free subset of .env syntax."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"").strip("'")
        if key:
            os.environ.setdefault(key, value)


@dataclass(frozen=True, slots=True)
class CrawlerConfig:
    requests_per_second: float = 2.0
    delay_between_requests: float = 0.5
    max_retries: int = 3
    timeout: float = 15.0
    database_url: str = "sqlite:///./data/products.db"
    cluster_similarity_threshold: float = 0.72
    minimum_cluster_size: int = 2
    cluster_algorithm: str = "connected_components"
    cluster_algorithm_version: str = "v1"
    cluster_similarity_engine: str = "tfidf"

    @classmethod
    def from_env(cls) -> "CrawlerConfig":
        return cls(
            requests_per_second=float(os.getenv("CRAWLER_REQUESTS_PER_SECOND", "2")),
            delay_between_requests=float(os.getenv("CRAWLER_DELAY_BETWEEN_REQUESTS", "0.5")),
            max_retries=int(os.getenv("CRAWLER_MAX_RETRIES", "3")),
            timeout=float(os.getenv("CRAWLER_TIMEOUT", "15")),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./data/products.db"),
            cluster_similarity_threshold=float(os.getenv("CLUSTER_SIMILARITY_THRESHOLD", "0.72")),
            minimum_cluster_size=int(os.getenv("CLUSTER_MINIMUM_SIZE", "2")),
            cluster_algorithm=os.getenv("CLUSTER_ALGORITHM", "connected_components"),
            cluster_algorithm_version=os.getenv("CLUSTER_ALGORITHM_VERSION", "v1"),
            cluster_similarity_engine=os.getenv("CLUSTER_SIMILARITY_ENGINE", "tfidf"),
        )

    @property
    def request_delay(self) -> float:
        rate_delay = 1 / self.requests_per_second if self.requests_per_second > 0 else 0
        return max(0, self.delay_between_requests, rate_delay)
