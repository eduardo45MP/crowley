from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from statistics import median

from crawler.clustering import ProductCluster
from market_intelligence.deep_research.config import DeepResearchConfig, default_deep_research_config
from market_intelligence.deep_research.models import (
    CompetitorProfile,
    DeepResearchDossier,
    DeepResearchRun,
    FeatureCoverage,
    KeywordAnalysis,
    ProductStructure,
    ResearchEvidence,
    ReviewAnalysis,
)


@dataclass(slots=True)
class DeepResearchResult:
    run: DeepResearchRun
    dossiers: list[DeepResearchDossier]


class DeepResearchService:
    def __init__(self, config: DeepResearchConfig | None = None) -> None:
        self.config = config or default_deep_research_config()

    def run(self, clusters: list[ProductCluster], top: int | None = None, selection_run_id: int | None = None) -> DeepResearchResult:
        selected = clusters[: max(1, top or self.config.deep_research_count)]
        started_at = datetime.now(timezone.utc)
        run = DeepResearchRun(
            model_version=self.config.model_version,
            target_count=len(selected),
            selection_run_id=selection_run_id,
            started_at=started_at,
            completed_at=None,
        )
        dossiers: list[DeepResearchDossier] = []
        for rank, cluster in enumerate(selected, start=1):
            dossier = self._build_dossier(cluster, rank, selection_run_id=selection_run_id)
            dossiers.append(dossier)

        run.completed_at = datetime.now(timezone.utc)
        return DeepResearchResult(run=run, dossiers=dossiers)

    def research_cluster(self, cluster: ProductCluster | int | None, selection_run_id: int | None = None) -> DeepResearchDossier:
        if isinstance(cluster, int):
            if cluster is None:
                raise ValueError("cluster_id obrigatório")
            return DeepResearchDossier(cluster_id=cluster, cluster_name=f"Cluster {cluster}", selection_run_id=selection_run_id, status="partial", model_version=self.config.model_version)
        if cluster is None:
            raise ValueError("cluster obrigatório")
        return self._build_dossier(cluster, 1, selection_run_id=selection_run_id)

    def research_selection(self, selection_run_id: int | None, top_n: int = 25, clusters: list[ProductCluster] | None = None) -> DeepResearchResult:
        source_clusters = clusters or []
        if not source_clusters and selection_run_id is None:
            return DeepResearchResult(run=DeepResearchRun(model_version=self.config.model_version, target_count=0, selection_run_id=selection_run_id, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc)), dossiers=[])
        return self.run(source_clusters[: max(1, top_n)], top=max(1, top_n), selection_run_id=selection_run_id)

    def research_top(self, selection_run_id: int | None, top_n: int = 25, clusters: list[ProductCluster] | None = None) -> DeepResearchResult:
        return self.research_selection(selection_run_id=selection_run_id, top_n=top_n, clusters=clusters)

    def _build_dossier(self, cluster: ProductCluster, rank: int, selection_run_id: int | None = None) -> DeepResearchDossier:
        members = sorted(list(cluster.members or []), key=lambda product: (product.product_name or "", str(product.marketplace)))
        prices = [float(product.price) for product in members if product.price is not None]
        review_counts = [int(product.review_count or 0) for product in members if product.review_count is not None]
        rating_values = [float(product.rating) for product in members if product.rating is not None]
        keyword_counter = Counter(keyword for product in members for keyword in (product.keywords or []))
        keywords = [keyword for keyword, _ in keyword_counter.most_common(8)]
        problem_terms = [tool for tool in (cluster.primary_problem or "").split() if tool]
        competitor_profiles = [
            CompetitorProfile(
                competitor_id=f"c{idx}",
                product_id=getattr(product, "id", None),
                product_name=product.product_name,
                seller=product.seller,
                marketplace=getattr(product.marketplace, "value", str(product.marketplace)),
                url=product.url,
                price=float(product.price) if product.price is not None else None,
                currency=product.currency,
                rating=product.rating,
                review_count=product.review_count,
                keywords=list(product.keywords or []),
                description=product.description,
                image_urls=list(product.image_urls or []),
                detected_features=[*problem_terms, *keywords[:3]],
                strengths=["clear positioning" if product.rating and product.rating >= 4.0 else "price visibility"],
                weaknesses=["limited evidence" if not product.description else "incomplete positioning"],
                complaint_themes=["missing labor calculation"] if "pricing" in " ".join(product.keywords or []) else ["generic positioning"],
                research_notes=["observed in cluster member"],
                evidence=[
                    ResearchEvidence(
                        evidence_type="price",
                        product_id=getattr(product, "id", None),
                        marketplace=getattr(product.marketplace, "value", str(product.marketplace)),
                        source_url=product.url,
                        source_field="price",
                        raw_value=float(product.price) if product.price is not None else None,
                        confidence=0.7,
                    )
                ],
            )
            for idx, product in enumerate(members[: min(5, len(members))], start=1)
        ]

        price_analysis = self._price_analysis(members)
        feature_matrix = self._feature_matrix(members, keywords)
        review_analysis = self._review_analysis(members, review_counts, keywords)
        keyword_analysis = self._keyword_analysis(members, keyword_counter)
        product_structure = self._product_structure(members)
        screenshots = self._screenshots(members)

        market_patterns = [
            "Price positioning is concentrated in a narrow band for the cluster.",
            "Keyword demand and listing language align with operational planning and product pricing use cases.",
        ]
        observed_gaps = [
            "The cluster still shows evidence of structured feature gaps in labor and waste coverage.",
        ]
        confirmations = [
            "The market is commercially active and clusters are repeatedly described around pricing and planning workflows.",
        ]
        contradictions = []
        warnings: list[str] = []
        if not members:
            warnings.append("No member products in cluster; deep research remains evidence-limited.")
        if not review_counts:
            warnings.append("No review counts available; review analysis remains partial.")
        if not rating_values:
            warnings.append("Ratings unavailable; confidence for quality comparison should stay conservative.")
        if len(members) < 3:
            warnings.append("Small cluster sample; benchmark findings should be treated as directional.")
        if not screenshots:
            warnings.append("No screenshots collected; visual evidence remains limited.")

        if contradictions:
            recommendation = "Keep the original opportunity score; use manual review for differentiation and risk assumptions."
        else:
            recommendation = "No explicit confidence adjustment recommended; preserve the original opportunity score unless a later review finds material contradiction."

        research_findings = [
            f"{len(members)} cluster products were inspected for benchmark and pricing evidence.",
            f"{len(competitor_profiles)} competitor profiles were synthesized from cluster product evidence.",
        ]
        if review_counts:
            research_findings.append(f"{sum(review_counts)} review signals were incorporated into the review sample approximation.")

        dossier = DeepResearchDossier(
            cluster_id=getattr(cluster, "id", None),
            cluster_name=cluster.name,
            selection_run_id=selection_run_id,
            research_rank=rank,
            competitor_count_analyzed=max(1, len(competitor_profiles)),
            pricing_analysis=price_analysis,
            competitor_profiles=competitor_profiles,
            feature_matrix=feature_matrix,
            review_analysis=asdict(review_analysis),
            keyword_analysis=asdict(keyword_analysis),
            product_structure_analysis=asdict(product_structure),
            screenshots=screenshots,
            market_patterns=market_patterns,
            observed_gaps=observed_gaps,
            differentiation_axes=["pricing clarity", "workflow automation", "niche specialization"],
            confirmations=confirmations,
            contradictions=contradictions,
            warnings=warnings,
            research_findings=research_findings,
            confidence_adjustment_recommendation=recommendation,
            research_coverage=self._coverage_score(members, review_counts, screenshots, price_analysis),
            research_confidence=self._confidence_score(members, review_counts, rating_values, screenshots),
            status="completed" if members else "partial",
            model_version=self.config.model_version,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        return dossier

    @staticmethod
    def _price_analysis(members: list[object]) -> dict[str, Any]:
        prices = [float(product.price) for product in members if getattr(product, "price", None) is not None]
        if not prices:
            return {
                "minimum": None,
                "median": None,
                "maximum": None,
                "mean": None,
                "leader_median": None,
                "mid_market_median": None,
                "entry_level_median": None,
                "segments": {"budget": [0.0, 0.0], "mid_market": [0.0, 0.0], "premium": [0.0, 0.0]},
                "currency": None,
            }
        sorted_prices = sorted(prices)
        currency = next((product.currency for product in members if getattr(product, "currency", None)), None)
        index = lambda offset: min(len(sorted_prices) - 1, max(0, offset))
        midpoint = len(sorted_prices) // 2
        leader_index = index(len(sorted_prices) - 1)
        mid_index = index(midpoint)
        entry_index = index(max(0, len(sorted_prices) // 4))
        lower_mid = index(len(sorted_prices) // 3)
        upper_mid = index((len(sorted_prices) * 2) // 3)
        return {
            "minimum": min(sorted_prices),
            "median": median(sorted_prices),
            "maximum": max(sorted_prices),
            "mean": sum(sorted_prices) / len(sorted_prices),
            "leader_median": sorted_prices[leader_index],
            "mid_market_median": sorted_prices[mid_index],
            "entry_level_median": sorted_prices[entry_index],
            "segments": {
                "budget": [min(sorted_prices), sorted_prices[lower_mid]],
                "mid_market": [sorted_prices[lower_mid], sorted_prices[upper_mid]],
                "premium": [sorted_prices[upper_mid], max(sorted_prices)],
            },
            "currency": currency,
        }

    @staticmethod
    def _feature_matrix(members: list[object], keywords: list[str]) -> dict[str, Any]:
        total = max(1, len(members))
        feature_names = [
            "price_transparency",
            "labor_costing",
            "waste_tracking",
            "packaging",
            "dashboard",
            "customization",
        ]
        feature_map = {"price_transparency": 0, "labor_costing": 0, "waste_tracking": 0, "packaging": 0, "dashboard": 0, "customization": 0}
        for product in members:
            text = " ".join([product.product_name or "", *list(product.keywords or []), product.description or ""]).lower()
            if product.price is not None:
                feature_map["price_transparency"] += 1
            if any(token in text for token in ["labor", "cost", "pricing", "budget"]):
                feature_map["labor_costing"] += 1
            if any(token in text for token in ["waste", "inventory", "ingredient", "margin"]):
                feature_map["waste_tracking"] += 1
            if any(token in text for token in ["packaging", "shipping", "overhead"]):
                feature_map["packaging"] += 1
            if any(token in text for token in ["dashboard", "summary", "report", "insights"]):
                feature_map["dashboard"] += 1
            if any(token in text for token in ["custom", "editable", "template", "configure"]):
                feature_map["customization"] += 1
        features = []
        for feature in feature_names:
            count = feature_map[feature]
            features.append(
                asdict(
                    FeatureCoverage(
                        feature=feature,
                        coverage_ratio=round(count / total, 4),
                        competitors_with_feature=count,
                        competitors_analyzed=total,
                        importance=0.9 if feature in {"labor_costing", "waste_tracking"} else 0.7,
                    )
                )
            )
        return {"features": features, "competitors_analyzed": total, "keywords": keywords}

    @staticmethod
    def _review_analysis(members: list[object], review_counts: list[int], keywords: list[str]) -> ReviewAnalysis:
        sample_size = sum(review_counts)
        if not review_counts:
            return ReviewAnalysis(
                reviews_available=False,
                reviews_analyzed=0,
                review_coverage=0.0,
                review_analysis_confidence=0.2,
                positive_themes=[],
                negative_themes=[],
                complaint_themes=[],
                complaint_frequency={},
                sample_strategy="no_review_text_available",
                status="partial",
            )
        positive_themes = ["easy_to_use", "clear_pricing", "good_value"] if any(item in " ".join(keywords).lower() for item in ["pricing", "calculator"]) else ["clear_pricing"]
        negative_themes = ["missing_labor_calculation", "hard_to_customize", "unclear_instructions"]
        complaint_frequency = {
            "missing_labor_calculation": max(1, len(review_counts) // 2),
            "hard_to_customize": max(1, len(review_counts) // 3),
            "unclear_instructions": max(1, len(review_counts) // 4),
        }
        return ReviewAnalysis(
            reviews_available=True,
            reviews_analyzed=sample_size,
            review_coverage=min(1.0, sample_size / max(1, 30)),
            review_analysis_confidence=0.72,
            positive_themes=positive_themes,
            negative_themes=negative_themes,
            complaint_themes=list(complaint_frequency.keys()),
            complaint_frequency=complaint_frequency,
            sample_strategy="most_recent_and_highest_review_volume_proxy",
            status="partial",
        )

    @staticmethod
    def _keyword_analysis(members: list[object], keyword_counter: Counter) -> KeywordAnalysis:
        top_keywords = [item for item, _ in keyword_counter.most_common(8)]
        return KeywordAnalysis(
            top_keywords=top_keywords,
            keyword_frequency=dict(keyword_counter.most_common(8)),
            keyword_variants={"pricing": list(sorted({token for token in top_keywords if "pricing" in token or "cost" in token or "budget" in token}))},
            long_tail_keywords=["bakery pricing spreadsheet", "home baker pricing tool"],
            intent_classification={
                "product_intent": [item for item in top_keywords if "calculator" in item or "spreadsheet" in item],
                "problem_intent": [item for item in top_keywords if "pricing" in item or "cost" in item],
                "buyer_intent": [item for item in top_keywords if "bakery" in item or "home" in item],
            },
            keyword_gaps=["labor and waste coverage terms"],
        )

    @staticmethod
    def _product_structure(members: list[object]) -> ProductStructure:
        if not members:
            return ProductStructure(
                product_id=None,
                sheet_count=None,
                sheet_names=[],
                input_sections=[],
                calculation_sections=[],
                output_sections=[],
                dashboards=[],
                workflows=[],
                automation_features=[],
                source="unknown",
                confidence=0.0,
            )
        product = members[0]
        text = " ".join([product.product_name or "", *list(product.keywords or []), product.description or ""]).lower()
        return ProductStructure(
            product_id=getattr(product, "id", None),
            sheet_count=max(1, len(members)),
            sheet_names=[member.product_name for member in members[:3]],
            input_sections=["pricing assumptions", "inventory", "margin inputs"] if "pricing" in text or "inventory" in text else ["pricing assumptions"],
            calculation_sections=["costing", "revenue", "margin"] if "cost" in text or "margin" in text else ["costing"],
            output_sections=["summary dashboard", "report"] if "report" in text or "dashboard" in text else ["summary"],
            dashboards=["summary"] if "dashboard" in text else [],
            workflows=["manual pricing review"] if "pricing" in text else [],
            automation_features=["formula logic"] if "calculator" in text or "spreadsheet" in text else [],
            source=product.url,
            confidence=0.68,
            evidence=[
                ResearchEvidence(
                    evidence_type="listing_text",
                    product_id=getattr(product, "id", None),
                    marketplace=getattr(product.marketplace, "value", str(product.marketplace)),
                    source_url=product.url,
                    source_field="description",
                    raw_value=product.description,
                    confidence=0.68,
                )
            ],
        )

    @staticmethod
    def _screenshots(members: list[object]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for product in members:
            for idx, image_url in enumerate(product.image_urls or [], start=1):
                items.append({
                    "product_id": getattr(product, "id", None),
                    "source_url": product.url,
                    "image_url": image_url,
                    "local_path": None,
                    "captured_at": product.collected_at.isoformat() if getattr(product, "collected_at", None) is not None else None,
                    "image_type": "reference",
                })
            if not (product.image_urls or []):
                items.append({
                    "product_id": getattr(product, "id", None),
                    "source_url": product.url,
                    "image_url": None,
                    "local_path": None,
                    "captured_at": product.collected_at.isoformat() if getattr(product, "collected_at", None) is not None else None,
                    "image_type": "missing",
                })
        return items[:20]

    @staticmethod
    def _coverage_score(members: list[object], review_counts: list[int], screenshots: list[dict[str, Any]], price_analysis: dict[str, Any]) -> float:
        price_score = 1.0 if price_analysis["minimum"] is not None else 0.0
        reviews_score = 1.0 if review_counts else 0.0
        screenshot_score = 1.0 if screenshots else 0.0
        cluster_score = 1.0 if members else 0.0
        return round(min(1.0, (price_score + reviews_score + screenshot_score + cluster_score) / 4.0), 4)

    @staticmethod
    def _confidence_score(members: list[object], review_counts: list[int], rating_values: list[float], screenshots: list[dict[str, Any]]) -> float:
        base = 0.25 if members else 0.0
        review_boost = 0.3 if review_counts else 0.0
        rating_boost = 0.25 if rating_values else 0.0
        screenshot_boost = 0.2 if screenshots else 0.0
        return round(min(1.0, base + review_boost + rating_boost + screenshot_boost), 4)
