from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from crawler.models import Product

PROMOTIONAL_STOPWORDS = {
    "digital",
    "download",
    "instant",
    "editable",
    "printable",
    "best",
    "seller",
    "bundle",
    "premium",
    "2026",
    "2025",
    "2024",
    "sale",
    "offer",
    "new",
    "popular",
    "etsy",
    "excel",
    "google",
    "kindle",
    "canva",
    "xlsx",
    "csv",
    "pdf",
}

PRODUCT_TYPE_TERMS = {
    "calculator": "calculator",
    "calculators": "calculator",
    "spreadsheet": "spreadsheet",
    "spreadsheets": "spreadsheet",
    "tracker": "tracker",
    "trackers": "tracker",
    "template": "template",
    "templates": "template",
    "planner": "planner",
    "workbook": "workbook",
    "tool": "tool",
    "sheet": "sheet",
}

PROBLEM_TERMS = {
    "pricing": "pricing",
    "price": "pricing",
    "cost": "costing",
    "costing": "costing",
    "budget": "budgeting",
    "budgeting": "budgeting",
    "roi": "roi",
    "return": "roi",
    "profit": "profit",
    "fee": "fee",
    "fees": "fee",
    "inventory": "inventory",
    "expense": "expense",
    "expenses": "expense",
    "commission": "commission",
    "pricing calculator": "pricing",
    "cost calculator": "costing",
}

_TAXONOMY_DIR = Path(__file__).resolve().parent.parent / "taxonomy"


def _taxon_terms(file_name: str) -> set[str]:
    path = _TAXONOMY_DIR / file_name
    if not path.exists():
        return set()
    try:
        values = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    if isinstance(values, list):
        return {str(item).strip().lower() for item in values if str(item).strip()}
    return set()


NICHE_TERMS = _taxon_terms("niches.json")


def _normalize_simple_plural(token: str) -> str:
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("sses") and len(token) > 5:
        return token[:-2]
    if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
        return token[:-1]
    return token


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "product-market"


def _normalize_cluster_token(raw: str) -> str:
    if not raw:
        return ""
    token = raw.strip().lower()
    token = re.sub(r"[^a-z0-9\s-]", " ", token)
    token = re.sub(r"\s+", " ", token).strip()
    token = _normalize_simple_plural(token)
    return token


def _tokenize(value: str | None) -> list[str]:
    if not value:
        return []
    tokens = []
    for chunk in re.split(r"[^a-z0-9]+", value.lower()):
        cleaned = _normalize_cluster_token(chunk)
        if cleaned and cleaned not in {" ", ""}:
            tokens.append(cleaned)
    return tokens


def _remove_noise(tokens: list[str]) -> list[str]:
    cleaned: list[str] = []
    for token in tokens:
        if token in PROMOTIONAL_STOPWORDS:
            continue
        if token in {"for", "and", "the", "with", "from", "your", "home", "custom", "shop", "online"}:
            continue
        cleaned.append(token)
    return cleaned


def build_clustering_text(product: Product) -> str:
    parts: list[str] = []
    if product.product_name:
        parts.append(product.product_name)
    if product.niche:
        parts.append(product.niche)
    if product.category:
        parts.append(product.category)
    if product.product_type is not None:
        parts.append(product.product_type.value)
    if product.keywords:
        parts.extend(product.keywords)
    if product.description:
        parts.append(product.description)

    tokens = []
    for part in parts:
        tokens.extend(_tokenize(part))
    tokens = _remove_noise(tokens)
    deduped: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token not in seen:
            seen.add(token)
            deduped.append(token)
    return " ".join(deduped)


@dataclass(slots=True)
class ProductClusterFeatures:
    normalized_text: str
    niche_terms: list[str]
    problem_terms: list[str]
    product_type_terms: list[str]
    keywords: list[str]

    @classmethod
    def from_product(cls, product: Product) -> "ProductClusterFeatures":
        normalized=build_clustering_text(product)
        tokens = _tokenize(normalized)
        niche_terms = _infer_niche_terms(product, tokens)
        problem_terms = _infer_problem_terms(tokens)
        product_type_terms = _infer_product_type_terms(tokens, product.product_type)
        keywords = _infer_keywords(tokens)
        return cls(
            normalized_text=normalized,
            niche_terms=niche_terms,
            problem_terms=problem_terms,
            product_type_terms=product_type_terms,
            keywords=keywords,
        )


def _infer_niche_terms(product: Product, tokens: list[str]) -> list[str]:
    found: list[str] = []
    if product.niche:
        found.append(product.niche.lower())
    for token in tokens:
        if token in NICHE_TERMS:
            found.append(token)
    if "bakery" in tokens:
        found.append("bakery")
    if "airbnb" in tokens:
        found.append("airbnb")
    if "wedding" in tokens:
        found.append("wedding")
    if "tattoo" in tokens or "ink" in tokens:
        found.append("tattoo artist")
    if "etsy" in tokens:
        found.append("etsy")
    return sorted(set(found), key=lambda value: (-len(value), value))


def _infer_problem_terms(tokens: list[str]) -> list[str]:
    matches: list[str] = []
    for token in tokens:
        lowered = token.strip()
        if lowered in PROBLEM_TERMS:
            matches.append(PROBLEM_TERMS[lowered])
    # keep common expressions when they are present in the raw text
    joined = " ".join(tokens)
    for phrase, canonical in PROBLEM_TERMS.items():
        if phrase in joined and canonical not in matches:
            matches.append(canonical)
    return sorted(set(matches), key=lambda value: (-len(value), value))


def _infer_product_type_terms(tokens: list[str], product_type: Any) -> list[str]:
    matches: list[str] = []
    if product_type is not None:
        value = str(product_type.value).lower()
        matches.append(value)
        canonical = PRODUCT_TYPE_TERMS.get(value, value)
        if canonical:
            matches.append(canonical)
    for token in tokens:
        if token in PRODUCT_TYPE_TERMS:
            matches.append(PRODUCT_TYPE_TERMS[token])
    return sorted(set(matches), key=lambda value: (-len(value), value))


def _infer_keywords(tokens: list[str]) -> list[str]:
    counts = Counter(tokens)
    ranked = []
    for token, count in counts.most_common():
        if token in PROMOTIONAL_STOPWORDS:
            continue
        if len(token) <= 2:
            continue
        if token in {"for", "and", "the", "with", "from", "your", "home", "custom", "shop", "online"}:
            continue
        ranked.append((token, count))

    phrases: list[str] = []
    for left, right in zip(tokens, tokens[1:]):
        bigram = f"{left} {right}"
        if left in {"custom", "home", "cake", "wedding", "airbnb", "bakery", "etsy", "tattoo"}:
            phrases.append(bigram)
        if right in {"pricing", "costing", "budget", "roi", "fee", "tracker", "sheet", "calculator"}:
            phrases.append(bigram)

    keywords = [token for token, _ in ranked[:8]]
    for phrase in phrases:
        if phrase not in keywords and phrase.count(" ") == 1:
            keywords.append(phrase)
    return keywords[:10]


class SimilarityEngine(Protocol):
    def fit(self, products: list[Product]) -> None:
        ...

    def similarity(self, a: Product, b: Product) -> float:
        ...


class TfidfSimilarityEngine:
    def __init__(self) -> None:
        self._products: list[Product] = []
        self._docs: list[str] = []
        self._idf: dict[str, float] = {}
        self._vocabulary: list[str] = []

    def fit(self, products: list[Product]) -> None:
        self._products = list(products)
        self._docs = [build_clustering_text(product) for product in self._products]
        tokens_by_doc = [self._tokenize_document(doc) for doc in self._docs]
        vocab = sorted({token for tokens in tokens_by_doc for token in tokens})
        self._vocabulary = vocab
        total_docs = max(len(tokens_by_doc), 1)
        for token in vocab:
            document_frequency = sum(1 for tokens in tokens_by_doc if token in tokens)
            self._idf[token] = math.log((total_docs + 1) / (document_frequency + 1)) + 1.0

    @staticmethod
    def _tokenize_document(doc: str) -> list[str]:
        return [token for token in _tokenize(doc) if token and token not in PROMOTIONAL_STOPWORDS]

    def similarity(self, a: Product, b: Product) -> float:
        if a is b and not self._products:
            return 1.0
        if not self._products:
            return 0.0
        left = self._vector_for_product(a)
        right = self._vector_for_product(b)
        dot = sum(left.get(key, 0.0) * right.get(key, 0.0) for key in set(left) | set(right))
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return max(0.0, min(1.0, dot / (left_norm * right_norm)))

    def _vector_for_product(self, product: Product) -> dict[str, float]:
        doc = build_clustering_text(product)
        tokens = self._tokenize_document(doc)
        counts = Counter(tokens)
        vector: dict[str, float] = {}
        total_tokens = max(sum(counts.values()), 1)
        for token, count in counts.items():
            tf = count / total_tokens
            if token not in self._idf:
                self._idf[token] = 1.0
            vector[token] = tf * self._idf[token]
        return vector


@dataclass(slots=True)
class ProductClusterMembership:
    product: Product
    membership_score: float = 0.0
    id: int | None = None
    cluster_id: int | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class ProductCluster:
    name: str
    slug: str
    niche: str | None = None
    product_type: str | None = None
    primary_problem: str | None = None
    secondary_problems: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    product_count: int = 0
    confidence: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    id: int | None = None
    run_id: int | None = None
    memberships: list[ProductClusterMembership] = field(default_factory=list)
    members: list[Product] = field(default_factory=list)


@dataclass(slots=True)
class ClusterRun:
    algorithm: str
    algorithm_version: str
    similarity_engine: str
    parameters: dict[str, Any] = field(default_factory=dict)
    product_count: int = 0
    cluster_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    id: int | None = None


@dataclass(slots=True)
class ClusterRunResult:
    run: ClusterRun
    clusters: list[ProductCluster]


def _dominant_vote(items: list[str]) -> str | None:
    if not items:
        return None
    counts = Counter(items)
    top_value, _ = counts.most_common(1)[0]
    return top_value


def _pluralize_product_type(value: str | None) -> str:
    if value is None:
        return "Products"
    mapping = {
        "calculator": "Calculators",
        "spreadsheet": "Spreadsheets",
        "tracker": "Trackers",
        "template": "Templates",
        "planner": "Planners",
        "tool": "Tools",
        "sheet": "Sheets",
    }
    return mapping.get(value.lower(), value.title())


def _dominant_niche(members: list[Product]) -> str | None:
    niche_values = [feature.niche_terms[0] if feature.niche_terms else None for feature in [ProductClusterFeatures.from_product(member) for member in members]]
    cleaned = [value for value in niche_values if value]
    if not cleaned:
        return None
    return _dominant_vote(cleaned)


def _build_cluster_metadata(members: list[Product]) -> tuple[str | None, str | None, str | None, list[str], list[str], float]:
    features = [ProductClusterFeatures.from_product(product) for product in members]
    niche_candidates = []
    problem_candidates = []
    product_type_candidates = []
    for feature in features:
        if feature.niche_terms:
            niche_candidates.append(feature.niche_terms[0])
        if feature.problem_terms:
            problem_candidates.extend(feature.problem_terms)
        if feature.product_type_terms:
            product_type_candidates.extend(feature.product_type_terms)
    niche = _dominant_vote(niche_candidates)
    problem = _dominant_vote(problem_candidates)
    product_type = _dominant_vote(product_type_candidates)
    if product_type:
        product_type = product_type.lower()

    secondary = sorted({item for item in problem_candidates if item and item != problem}, key=lambda value: (-len(value), value))[:3]
    keywords = []
    keyword_counter: Counter[str] = Counter()
    for feature in features:
        keyword_counter.update(feature.keywords)
    for key, _ in keyword_counter.most_common(12):
        if key not in {"calculator", "spreadsheet", "tracker", "template", "planner", "tool", "sheet", "pricing", "costing", "budget", "fee", "roi", "inventory"}:
            keywords.append(key)
    if not keywords:
        for feature in features:
            keywords.extend(feature.keywords)
    confidence = 0.0
    if len(members) > 1:
        engine = TfidfSimilarityEngine()
        engine.fit(members)
        pair_scores = []
        for index, left in enumerate(members):
            for right in members[index + 1 :]:
                pair_scores.append(engine.similarity(left, right))
        confidence = sum(pair_scores) / len(pair_scores) if pair_scores else 0.0
    elif members:
        confidence = 1.0
    return niche, product_type, problem, secondary, keywords[:10], round(max(0.0, min(1.0, confidence)), 4)


def _make_cluster_name(members: list[Product]) -> str:
    niche, product_type, problem, _, _, _ = _build_cluster_metadata(members)
    product_label = _pluralize_product_type(product_type)
    if niche and problem and product_type:
        return f"{niche.title()} {problem.title()} {product_label}"
    if niche and product_type:
        return f"{niche.title()} {product_label}"
    if niche and problem:
        return f"{niche.title()} {problem.title()}"
    if product_type:
        return f"{product_label}"
    if members:
        return members[0].product_name.strip()
    return "Product Market"


def _infer_cluster_membership_scores(cluster_members: list[Product], anchor: Product) -> list[float]:
    engine = TfidfSimilarityEngine()
    engine.fit(cluster_members)
    scores = []
    for member in cluster_members:
        scores.append(engine.similarity(anchor, member))
    return scores


def _build_cluster_from_members(members: list[Product]) -> ProductCluster:
    niche, product_type, problem, secondary, keywords, confidence = _build_cluster_metadata(members)
    name = _make_cluster_name(members)
    cluster = ProductCluster(
        name=name,
        slug=_slugify(name),
        niche=niche,
        product_type=product_type,
        primary_problem=problem,
        secondary_problems=secondary,
        keywords=keywords,
        product_count=len(members),
        confidence=confidence,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        members=list(members),
    )
    for member in members:
        cluster.memberships.append(
            ProductClusterMembership(
                product=member,
                membership_score=max(0.0, min(1.0, confidence if len(members) > 1 else 1.0)),
                created_at=cluster.created_at,
            )
        )
    return cluster


def _connected_components(products: list[Product], threshold: float) -> list[list[Product]]:
    if not products:
        return []
    engine = TfidfSimilarityEngine()
    engine.fit(products)
    assigned: set[int] = set()
    groups: list[list[Product]] = []
    for index in range(len(products)):
        if index in assigned:
            continue
        queue = [index]
        component: list[Product] = []
        while queue:
            current = queue.pop()
            if current in assigned:
                continue
            assigned.add(current)
            component.append(products[current])
            for candidate in range(len(products)):
                if candidate in assigned:
                    continue
                if engine.similarity(products[current], products[candidate]) >= threshold:
                    queue.append(candidate)
        groups.append(component)
    return groups


def cluster_products(products: list[Product], similarity_threshold: float = 0.72, minimum_cluster_size: int = 2) -> list[ProductCluster]:
    if not products:
        return []
    groups = _connected_components(products, similarity_threshold)
    clusters: list[ProductCluster] = []
    for group in groups:
        if len(group) >= minimum_cluster_size or len(group) == 1:
            clusters.append(_build_cluster_from_members(group))
    return sorted(clusters, key=lambda cluster: (-cluster.product_count, -float(cluster.confidence or 0.0), cluster.name.lower()))
