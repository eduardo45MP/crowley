from __future__ import annotations

from market_intelligence.deep_research.competitor_analysis import CompetitorBenchmarkSelector
from market_intelligence.deep_research.config import DeepResearchConfig, default_deep_research_config
from market_intelligence.deep_research.keyword_analysis import KeywordAnalyzer
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
from market_intelligence.deep_research.product_structure import ProductStructureAnalyzer
from market_intelligence.deep_research.repositories import DeepResearchRepository, InMemoryDeepResearchRepository
from market_intelligence.deep_research.review_analysis import ReviewAnalyzer
from market_intelligence.deep_research.screenshots import ScreenshotCollector
from market_intelligence.deep_research.service import DeepResearchService

__all__ = [
    "CompetitorBenchmarkSelector",
    "CompetitorProfile",
    "DeepResearchConfig",
    "DeepResearchDossier",
    "DeepResearchRepository",
    "DeepResearchRun",
    "DeepResearchService",
    "FeatureCoverage",
    "InMemoryDeepResearchRepository",
    "KeywordAnalysis",
    "KeywordAnalyzer",
    "ProductStructure",
    "ProductStructureAnalyzer",
    "ResearchEvidence",
    "ReviewAnalysis",
    "ReviewAnalyzer",
    "ScreenshotCollector",
    "default_deep_research_config",
]
