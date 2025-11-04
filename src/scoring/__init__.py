"""
FEAT-003: Lead Scoring Module

This module implements ICP (Ideal Customer Profile) fit scoring for veterinary practices.

Components:
- lead_scorer: Core scoring calculator with 5 components
- classifier: Practice size and priority tier classification
- scoring_orchestrator: Workflow orchestration with circuit breaker

Usage:
    from src.scoring import LeadScorer, ScoringOrchestrator
    from src.integrations.notion_scoring import NotionScoringClient

    # Initialize
    scorer = LeadScorer()
    notion_client = NotionScoringClient(api_key, database_id)
    orchestrator = ScoringOrchestrator(notion_client, scorer)

    # Score single practice
    result = orchestrator.score_practice(practice_id)

    # Score batch
    results = orchestrator.score_batch(practice_ids)
"""

from src.scoring.lead_scorer import LeadScorer
from src.scoring.classifier import PracticeClassifier
from src.scoring.scoring_orchestrator import ScoringOrchestrator

__all__ = [
    "LeadScorer",
    "PracticeClassifier",
    "ScoringOrchestrator",
]
