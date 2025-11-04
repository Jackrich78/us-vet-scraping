# FEAT-002 Integration Guide for FEAT-003 Builder

**Document Purpose:** Provide concrete implementation guidance for integrating FEAT-003 scoring into FEAT-002 enrichment pipeline.

**Critical Context:** FEAT-003 owns implementing the auto-trigger mechanism. FEAT-002 provides the hook points, but FEAT-003 writes the integration code.

---

## Integration Point: EnrichmentOrchestrator

### FEAT-002's Responsibility (Already Implemented/To Be Implemented)

**File:** `src/enrichment/enrichment_orchestrator.py`

**What FEAT-002 Must Provide:**

```python
from typing import Optional, Protocol
from src.scoring.scoring_service import ScoringService  # FEAT-003 component

class EnrichmentOrchestrator:
    """
    Orchestrates website enrichment with optional scoring integration.

    FEAT-002 owns this class. FEAT-003 provides ScoringService via dependency injection.
    """

    def __init__(
        self,
        website_scraper: WebsiteScraper,
        llm_extractor: LLMExtractor,
        notion_client: NotionClient,
        error_tracker: ErrorAggregator,
        cost_tracker: CostTracker,
        scoring_service: Optional[ScoringService] = None,  # ← FEAT-003 integration point
        config: EnrichmentConfig
    ):
        self.website_scraper = website_scraper
        self.llm_extractor = llm_extractor
        self.notion_client = notion_client
        self.error_tracker = error_tracker
        self.cost_tracker = cost_tracker
        self.scoring_service = scoring_service  # ← Store for later use
        self.config = config

    async def enrich_all_practices(self, test_mode: bool = False) -> Dict[str, Any]:
        """
        Enrich practices with website data.

        Integration Point: After enrichment succeeds, call scoring_service if provided.
        """
        # ... enrichment logic ...

        # FEAT-002 provides this hook point for FEAT-003:
        for extraction in extracted_data:
            try:
                # Update Notion with enrichment data
                notion_client.update_practice_enrichment(
                    page_id=extraction.notion_page_id,
                    enrichment_data=extraction
                )

                # ═══════════════════════════════════════════════════
                # INTEGRATION POINT: Call FEAT-003 scoring if enabled
                # ═══════════════════════════════════════════════════
                if self.config.auto_trigger_scoring and self.scoring_service:
                    await self._trigger_scoring(extraction)  # ← Hook point
                # ═══════════════════════════════════════════════════

            except NotionAPIError as e:
                error_tracker.log_error("notion_update", str(e), extraction.practice_name)

    async def _trigger_scoring(self, extraction: VetPracticeExtraction) -> None:
        """
        Hook point for FEAT-003 auto-trigger.

        FEAT-002 provides this method signature.
        FEAT-003 implements the actual ScoringService.calculate_icp_score() call.

        Critical Requirements:
        - Must catch ALL exceptions (don't propagate to enrichment loop)
        - Must complete within 5 seconds (timeout enforced by FEAT-003)
        - Must log errors but continue enrichment pipeline
        """
        try:
            # FEAT-003 implements this method in ScoringService:
            score_result = await self.scoring_service.calculate_icp_score(
                practice_id=extraction.notion_page_id,
                google_maps_data=extraction.google_maps_data,  # ← FEAT-002 must pass this
                enrichment_data=extraction  # ← FEAT-002 passes enrichment result
            )

            # FEAT-003 implements this method in NotionClient extension:
            await self.notion_client.update_practice_score(
                practice_id=extraction.notion_page_id,
                score_result=score_result
            )

            logger.info(f"Scored {extraction.practice_name}: {score_result.lead_score}/120")

        except Exception as e:
            # Catch ALL exceptions - scoring failures must not break enrichment
            logger.error(f"Scoring failed for {extraction.practice_name}: {e}")
            self.error_tracker.log_error("scoring_trigger", str(e), extraction.practice_name)
            # DO NOT re-raise - enrichment pipeline must continue
```

---

## Integration Point: main.py Orchestration

### Who Creates the ScoringService Instance?

**File:** `main.py` (or `src/main.py`)

**FEAT-003's Responsibility:**

```python
import asyncio
from src.config.config import load_config
from src.enrichment.enrichment_orchestrator import EnrichmentOrchestrator
from src.scoring.scoring_service import ScoringService  # ← FEAT-003 component
from src.scoring.score_calculator import ScoreCalculator  # ← FEAT-003 component
from src.utils.logging import setup_logger

async def main():
    """Main entry point for enrichment + scoring pipeline."""

    # Load configuration
    config = load_config("config/config.json")
    logger = setup_logger(config.logging)

    # Initialize FEAT-002 components
    website_scraper = WebsiteScraper(config.website_scraping)
    llm_extractor = LLMExtractor(config.website_scraping, cost_tracker)
    notion_client = NotionClient(config.notion)
    error_tracker = ErrorAggregator()
    cost_tracker = CostTracker(max_budget=config.enrichment.cost_threshold)

    # ═══════════════════════════════════════════════════════════════
    # FEAT-003 Integration: Create ScoringService if enabled
    # ═══════════════════════════════════════════════════════════════
    scoring_service = None
    if config.enrichment.auto_trigger_scoring:
        logger.info("Auto-trigger scoring enabled - initializing ScoringService")

        # FEAT-003 components:
        score_calculator = ScoreCalculator(config.scoring)
        confidence_evaluator = ConfidenceEvaluator(config.scoring)
        tier_classifier = TierClassifier(config.scoring)
        breakdown_generator = BreakdownGenerator()
        circuit_breaker = CircuitBreaker(
            fail_max=config.scoring.circuit_breaker_fail_max,
            reset_timeout=config.scoring.circuit_breaker_reset_timeout
        )

        # Assemble FEAT-003 ScoringService:
        scoring_service = ScoringService(
            score_calculator=score_calculator,
            confidence_evaluator=confidence_evaluator,
            tier_classifier=tier_classifier,
            breakdown_generator=breakdown_generator,
            circuit_breaker=circuit_breaker,
            notion_client=notion_client,  # Shared with FEAT-002
            config=config.scoring
        )
    else:
        logger.info("Auto-trigger scoring disabled")
    # ═══════════════════════════════════════════════════════════════

    # Initialize FEAT-002 EnrichmentOrchestrator with optional scoring
    orchestrator = EnrichmentOrchestrator(
        website_scraper=website_scraper,
        llm_extractor=llm_extractor,
        notion_client=notion_client,
        error_tracker=error_tracker,
        cost_tracker=cost_tracker,
        scoring_service=scoring_service,  # ← Inject FEAT-003 service (or None)
        config=config.enrichment
    )

    # Run enrichment pipeline (with optional auto-scoring)
    result = await orchestrator.enrich_all_practices(test_mode=args.test)

    # Log results
    logger.info(f"Enrichment complete: {result['enriched']} practices")
    if scoring_service:
        logger.info(f"Scoring complete: {result.get('scored', 0)} practices")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Integration Point: Manual Rescore Command

### CLI Entry Point for Manual Rescoring

**File:** `main.py` (extend with --rescore flag)

**FEAT-003's Responsibility:**

```python
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Vet Lead Generation Pipeline")
    parser.add_argument("--test", action="store_true", help="Test mode (10 practices)")
    parser.add_argument("--rescore", nargs="?", const="all", help="Rescore practices (all or practice-id)")
    return parser.parse_args()

async def main():
    args = parse_args()
    config = load_config("config/config.json")

    # ═══════════════════════════════════════════════════════════════
    # FEAT-003: Handle manual rescore command
    # ═══════════════════════════════════════════════════════════════
    if args.rescore:
        logger.info(f"Manual rescore requested: {args.rescore}")

        # Initialize FEAT-003 components (no FEAT-002 components needed)
        notion_client = NotionClient(config.notion)
        scoring_service = ScoringService(
            score_calculator=ScoreCalculator(config.scoring),
            confidence_evaluator=ConfidenceEvaluator(config.scoring),
            tier_classifier=TierClassifier(config.scoring),
            breakdown_generator=BreakdownGenerator(),
            circuit_breaker=CircuitBreaker(...),
            notion_client=notion_client,
            config=config.scoring
        )

        # Rescore CLI handler (FEAT-003 implementation)
        from src.scoring.rescore_cli import RescoreCLI
        cli = RescoreCLI(scoring_service, notion_client, config.scoring)

        if args.rescore == "all":
            result = await cli.rescore_all()
        else:
            result = await cli.rescore_single(practice_id=args.rescore)

        logger.info(f"Rescore complete: {result['scored']} practices, {result['failed']} failures")
        return
    # ═══════════════════════════════════════════════════════════════

    # Normal enrichment flow...
    orchestrator = EnrichmentOrchestrator(...)
    result = await orchestrator.enrich_all_practices(test_mode=args.test)
```

---

## Data Contract: What FEAT-002 Must Pass to FEAT-003

### VetPracticeExtraction Model Requirements

**CRITICAL:** FEAT-002's `VetPracticeExtraction` model must include a reference to the original Google Maps data.

**File:** `src/models/enrichment_models.py` (or wherever FEAT-002 defines this)

```python
from pydantic import BaseModel
from typing import Optional
from src.models.apify_models import VeterinaryPractice  # ← Google Maps data

class VetPracticeExtraction(BaseModel):
    """
    Enrichment data extracted from website by FEAT-002.

    FEAT-003 Requirement: Must include google_maps_data reference for baseline scoring.
    """

    # Notion reference
    notion_page_id: str

    # ═══════════════════════════════════════════════════════════════
    # FEAT-003 Dependency: Original Google Maps data needed for baseline scoring
    # ═══════════════════════════════════════════════════════════════
    google_maps_data: VeterinaryPractice  # ← FEAT-002 must populate this
    # ═══════════════════════════════════════════════════════════════

    # Vet count
    vet_count_total: Optional[int] = None
    vet_count_confidence: Literal["high", "medium", "low"] = "low"

    # Decision maker
    decision_maker: Optional[DecisionMaker] = None

    # Services (multi-select)
    emergency_24_7: bool = False
    specialty_services: List[str] = Field(default_factory=list)
    wellness_programs: bool = False
    boarding_services: bool = False

    # Technology indicators
    online_booking: bool = False
    telemedicine: bool = False
    patient_portal: bool = False
    digital_records_mentioned: bool = False

    # Personalization context
    personalization_context: List[str] = Field(default_factory=list)
    awards_accreditations: List[str] = Field(default_factory=list)
    unique_services: List[str] = Field(default_factory=list)

    # Metadata
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**Why google_maps_data is required:**
- FEAT-003 needs Google review count for call volume scoring
- FEAT-003 needs Google rating for baseline quality scoring
- FEAT-003 needs "has website" field for baseline scoring
- FEAT-003 needs "has multiple locations" field for call volume scoring

If FEAT-002 doesn't include this, FEAT-003 would need to re-query Notion (inefficient) or fail gracefully (missing baseline score).

---

## Configuration Schema: Coordinated Settings

### config.json Structure

```json
{
  "enrichment": {
    "auto_trigger_scoring": true,  // ← FEAT-002 reads this, FEAT-003 respects it
    "cost_threshold": 1.00,
    "re_enrichment_days": 30
  },
  "scoring": {
    "timeout_seconds": 5,
    "confidence_penalty_enabled": true,
    "confidence_penalty_weights": {
      "high": 1.0,
      "medium": 0.9,
      "low": 0.7
    },
    "sweet_spot_min_vets": 3,
    "sweet_spot_max_vets": 8,
    "circuit_breaker_fail_max": 5,
    "circuit_breaker_reset_timeout": 60,
    "multiple_locations_points": 10
  }
}
```

**Coordination Point:** Both FEAT-002 and FEAT-003 read `config.enrichment.auto_trigger_scoring`.

---

## Testing the Integration

### Unit Test: Verify Hook Point (FEAT-003 Responsibility)

**File:** `tests/integration/test_feat002_feat003_integration.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.enrichment.enrichment_orchestrator import EnrichmentOrchestrator
from src.scoring.scoring_service import ScoringService

@pytest.mark.asyncio
async def test_auto_trigger_calls_scoring_service():
    """
    Verify EnrichmentOrchestrator._trigger_scoring() calls ScoringService.

    Acceptance Criteria: AC-FEAT-003-043 (auto-trigger enabled)
    """
    # Mock FEAT-003 ScoringService
    mock_scoring_service = AsyncMock(spec=ScoringService)
    mock_scoring_service.calculate_icp_score.return_value = MagicMock(
        lead_score=85,
        priority_tier="Hot"
    )

    # Mock FEAT-002 components
    mock_notion_client = AsyncMock()

    # Create EnrichmentOrchestrator with scoring enabled
    config = MagicMock()
    config.auto_trigger_scoring = True  # ← Integration point enabled

    orchestrator = EnrichmentOrchestrator(
        website_scraper=MagicMock(),
        llm_extractor=MagicMock(),
        notion_client=mock_notion_client,
        error_tracker=MagicMock(),
        cost_tracker=MagicMock(),
        scoring_service=mock_scoring_service,  # ← Inject FEAT-003 service
        config=config
    )

    # Create mock extraction
    extraction = MagicMock()
    extraction.notion_page_id = "test-page-id"
    extraction.practice_name = "Test Practice"

    # Call hook point
    await orchestrator._trigger_scoring(extraction)

    # Verify FEAT-003 ScoringService was called
    mock_scoring_service.calculate_icp_score.assert_called_once_with(
        practice_id="test-page-id",
        google_maps_data=extraction.google_maps_data,
        enrichment_data=extraction
    )

    # Verify Notion was updated with score
    mock_notion_client.update_practice_score.assert_called_once()
```

---

## Checklist for FEAT-003 Builder

When implementing FEAT-003, ensure:

- [ ] `ScoringService` class created in `src/scoring/scoring_service.py`
- [ ] `ScoringService.calculate_icp_score()` method signature matches FEAT-002's expectation
- [ ] `ScoreCalculator` handles missing `google_maps_data` gracefully (Scenario D)
- [ ] `NotionClient.update_practice_score()` extension added
- [ ] `RescoreCLI` class created for manual rescore command
- [ ] `main.py` instantiates `ScoringService` when `auto_trigger_scoring=true`
- [ ] `main.py` handles `--rescore` flag
- [ ] Integration tests verify `EnrichmentOrchestrator._trigger_scoring()` is called
- [ ] Circuit breaker is initialized with config values
- [ ] Timeout enforcement (5 seconds) implemented in `ScoringService`
- [ ] All exceptions caught in `_trigger_scoring()` (don't propagate to FEAT-002)

---

## Summary: Who Owns What

| Component | Owner | Location |
|-----------|-------|----------|
| `EnrichmentOrchestrator` class | FEAT-002 | `src/enrichment/enrichment_orchestrator.py` |
| `EnrichmentOrchestrator._trigger_scoring()` method | FEAT-002 (signature), FEAT-003 (called service) | Same file |
| `ScoringService` class | FEAT-003 | `src/scoring/scoring_service.py` |
| `ScoringService.calculate_icp_score()` implementation | FEAT-003 | Same file |
| `NotionClient.update_practice_score()` extension | FEAT-003 | `src/integrations/notion_mapper.py` (or similar) |
| `RescoreCLI` class | FEAT-003 | `src/scoring/rescore_cli.py` |
| `main.py` ScoringService instantiation | FEAT-003 | `main.py` |
| `main.py` --rescore flag handling | FEAT-003 | `main.py` |
| VetPracticeExtraction.google_maps_data field | FEAT-002 (must provide), FEAT-003 (requires) | `src/models/enrichment_models.py` |

**Integration Philosophy:** FEAT-002 provides hook points (dependency injection, `_trigger_scoring()` method). FEAT-003 implements the services that plug into those hooks.

---

**Document Status:** Ready for FEAT-003 builder to implement auto-trigger integration
**Next Step:** `/build FEAT-003` with this integration guide
