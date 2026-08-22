from __future__ import annotations

import math
from collections import Counter
from decimal import Decimal, InvalidOperation

from crawler.clustering import ProductCluster
from crawler.models import Product
from market_intelligence.competition.models import CompetitionFeatures


def _safe_decimal(value: Decimal | float | int | str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


class CompetitionFeatureExtractor:
    def extract(self, cluster: ProductCluster) -> CompetitionFeatures:
        members = list(cluster.members or [])
        if not members and cluster.product_count:
            members = list(cluster.members)

        competitor_count = len(members) if members else max(0, cluster.product_count)
        seller_counts = Counter()
        seller_review_counts: dict[str, int] = {}
        marketplace_set: set[str] = set()
        pricing_values: list[Decimal] = []
        review_values: list[int] = []
        rating_values: list[float] = []
        description_lengths: list[int] = []
        keyword_tokens: list[str] = []

        for product in members:
            if product.marketplace:
                marketplace_set.add(product.marketplace.value)
            seller_name = (product.seller or "unknown").strip() or "unknown"
            seller_counts[seller_name] += 1
            seller_review_counts[seller_name] = seller_review_counts.get(seller_name, 0) + int(product.review_count or 0)
            review_values.append(int(product.review_count or 0))
            if product.price is not None:
                pricing_values.append(product.price)
            if product.rating is not None:
                rating_values.append(float(product.rating))
            if product.description:
                description_lengths.append(len(product.description.strip().split()))
            keyword_tokens.extend(item.lower() for item in (product.keywords or []))

        seller_count = len(seller_counts)
        top_seller_listing_share = self._share_for_top_count(seller_counts)
        top_seller_review_share = self._share_for_top_review(seller_review_counts, sum(review_values))
        top_3_review_share = self._top_n_review_share(seller_review_counts, sum(review_values), 3)

        market_fragmentation = self._fragmentation_score(top_seller_listing_share, top_3_review_share)
        price_stats = self._price_stats(pricing_values)

        price_compression = None
        if price_stats["mean"] is not None and price_stats["mean"] > 0:
            price_compression = self._price_compression(price_stats["mean"], price_stats["stddev"])

        price_band_opportunity = None
        if price_stats["min"] is not None and price_stats["max"] is not None and price_stats["min"] != price_stats["max"]:
            price_band_opportunity = self._price_band_opportunity(price_stats["min"], price_stats["median"], price_stats["max"])

        quality_signal = None
        if rating_values:
            mean_rating = sum(rating_values) / len(rating_values)
            quality_signal = min(1.0, max(0.0, (mean_rating / 5.0) * 0.8 + (len(rating_values) / max(1, competitor_count)) * 0.2))
        product_depth_signal = self._product_depth_signal(description_lengths, keyword_tokens, competitor_count)
        observed_differentiation_signal = self._observed_differentiation_signal(keyword_tokens, competitor_count)

        return CompetitionFeatures(
            competitor_count=competitor_count,
            seller_count=seller_count,
            marketplace_count=len(marketplace_set),
            top_seller_listing_share=top_seller_listing_share,
            top_seller_review_share=top_seller_review_share,
            top_3_review_share=top_3_review_share,
            market_fragmentation=market_fragmentation,
            price_min=price_stats["min"],
            price_median=price_stats["median"],
            price_max=price_stats["max"],
            price_mean=price_stats["mean"],
            price_stddev=price_stats["stddev"],
            price_cv=price_stats["cv"],
            price_compression=price_compression,
            price_band_opportunity=price_band_opportunity,
            rating_mean=(sum(rating_values) / len(rating_values)) if rating_values else None,
            rating_median=self._median(rating_values) if rating_values else None,
            competitor_quality_signal=quality_signal,
            visual_quality_signal=None,
            product_depth_signal=product_depth_signal,
            observed_differentiation_signal=observed_differentiation_signal,
        )

    @staticmethod
    def _share_for_top_count(counter: Counter[str]) -> float | None:
        if not counter:
            return None
        total = sum(counter.values())
        if total == 0:
            return None
        return max(counter.values()) / total

    @staticmethod
    def _share_for_top_review(review_counts: dict[str, int], total_reviews: int) -> float | None:
        if not review_counts or total_reviews <= 0:
            return None
        return max(review_counts.values()) / total_reviews

    @staticmethod
    def _top_n_review_share(review_counts: dict[str, int], total_reviews: int, top_n: int) -> float | None:
        if not review_counts or total_reviews <= 0:
            return None
        ranked = sorted(review_counts.values(), reverse=True)[:top_n]
        if not ranked:
            return None
        return sum(ranked) / total_reviews

    @staticmethod
    def _fragmentation_score(top_seller_listing_share: float | None, top_3_review_share: float | None) -> float | None:
        if top_seller_listing_share is None and top_3_review_share is None:
            return None
        concentration = 0.0
        if top_seller_listing_share is not None:
            concentration += top_seller_listing_share * 0.6
        if top_3_review_share is not None:
            concentration += top_3_review_share * 0.4
        return max(0.0, min(1.0, 1.0 - concentration))

    @staticmethod
    def _median(values: list[float]) -> float | None:
        if not values:
            return None
        ordered = sorted(values)
        middle = len(ordered) // 2
        if len(ordered) % 2 == 0:
            return (ordered[middle - 1] + ordered[middle]) / 2.0
        return float(ordered[middle])

    @staticmethod
    def _price_stats(values: list[Decimal]) -> dict[str, Decimal | float | None]:
        if not values:
            return {
                "min": None,
                "median": None,
                "max": None,
                "mean": None,
                "stddev": None,
                "cv": None,
            }
        ordered = sorted(values)
        total = sum(ordered, Decimal("0"))
        mean = total / Decimal(len(ordered))
        variance = sum((value - mean) ** 2 for value in ordered) / Decimal(len(ordered))
        stddev = variance.sqrt()
        cv = None
        if mean > 0:
            cv = float((stddev / mean))
        return {
            "min": ordered[0],
            "median": CompetitionFeatureExtractor._median_decimal(ordered),
            "max": ordered[-1],
            "mean": mean,
            "stddev": stddev,
            "cv": cv,
        }

    @staticmethod
    def _median_decimal(values: list[Decimal]) -> Decimal:
        middle = len(values) // 2
        if len(values) % 2 == 0:
            return (values[middle - 1] + values[middle]) / Decimal(2)
        return values[middle]

    @staticmethod
    def _price_compression(mean: Decimal | None, stddev: Decimal | None) -> float | None:
        if mean is None or stddev is None or mean <= 0:
            return None
        return max(0.0, min(1.0, float(stddev / mean)))

    @staticmethod
    def _price_band_opportunity(price_min: Decimal | None, price_median: Decimal | None, price_max: Decimal | None) -> float | None:
        if price_min is None or price_median is None or price_max is None:
            return None
        if price_max <= price_min:
            return 0.0
        spread = float(price_max - price_min)
        midpoint = float(price_median - price_min)
        base = midpoint / max(spread, 1e-9)
        return max(0.0, min(1.0, base * 0.9 + 0.1))

    @staticmethod
    def _product_depth_signal(description_lengths: list[int], keyword_tokens: list[str], competitor_count: int) -> float | None:
        if not description_lengths and not keyword_tokens:
            return None
        avg_words = sum(description_lengths) / len(description_lengths) if description_lengths else 0.0
        avg_keywords = len(keyword_tokens) / max(1, competitor_count)
        return max(0.0, min(1.0, (avg_words / 80.0) * 0.7 + (avg_keywords / 12.0) * 0.3))

    @staticmethod
    def _observed_differentiation_signal(keyword_tokens: list[str], competitor_count: int) -> float | None:
        if not keyword_tokens or competitor_count <= 0:
            return None
        counter = Counter(keyword_tokens)
        repetition = sum(count for count in counter.values() if count > 1)
        total = len(keyword_tokens)
        if total == 0:
            return None
        overlap = repetition / total
        return max(0.0, min(1.0, 1.0 - overlap))
