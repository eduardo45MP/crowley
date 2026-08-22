"""Opportunity scoring engine for aggregating independent market-intelligence dimensions."""

from market_intelligence.opportunity.config import OpportunityScoreConfig
from market_intelligence.opportunity.models import OpportunityAnalysis, OpportunityInputs, OpportunityScoreResult
from market_intelligence.opportunity.service import OpportunityAnalysisService

__all__ = [
    "OpportunityAnalysis",
    "OpportunityInputs",
    "OpportunityScoreResult",
    "OpportunityScoreConfig",
    "OpportunityAnalysisService",
]
