"""
Scoring Orchestrator for FEAT-003.

Coordinates the complete scoring workflow:
1. Fetch data from Notion (Google Maps + enrichment)
2. Calculate ICP fit score
3. Update Notion with results

Supports:
- Single practice scoring
- Batch scoring
- Auto-trigger from FEAT-002
- Manual rescore via CLI
- Timeout enforcement (5 seconds per practice)
- Circuit breaker pattern
"""

import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime

from src.scoring.lead_scorer import LeadScorer
from src.integrations.notion_scoring import NotionScoringClient
from src.models.scoring_models import (
    ScoringInput,
    ScoringResult,
    ScoringTimeoutError,
    CircuitBreakerError,
    ScoringValidationError
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ScoringOrchestrator:
    """
    Orchestrates lead scoring workflow.

    Responsibilities:
    - Fetch practice data from Notion (2 queries: Google Maps + enrichment)
    - Calculate ICP fit score using LeadScorer
    - Update Notion with scoring results
    - Enforce 5-second timeout per practice
    - Handle errors gracefully with circuit breaker
    - Support batch processing with progress tracking

    Usage:
        orchestrator = ScoringOrchestrator(
            notion_client=notion_client,
            scorer=lead_scorer
        )

        # Score single practice
        result = orchestrator.score_practice(practice_id)

        # Score batch
        results = orchestrator.score_batch(practice_ids)
    """

    # Timeout for scoring a single practice
    SCORING_TIMEOUT_SECONDS = 5.0

    def __init__(
        self,
        notion_client: NotionScoringClient,
        scorer: Optional[LeadScorer] = None
    ):
        """Initialize scoring orchestrator.

        Args:
            notion_client: Notion client for data fetching and updates
            scorer: Lead scorer instance (creates new if not provided)
        """
        self.notion_client = notion_client
        self.scorer = scorer or LeadScorer()

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.logger.info("ScoringOrchestrator initialized")

    async def score_practice_async(self, practice_id: str) -> ScoringResult:
        """
        Score a single practice with timeout enforcement.

        Workflow:
        1. Fetch Google Maps data (Notion query 1)
        2. Fetch enrichment data (Notion query 2)
        3. Calculate ICP fit score
        4. Update Notion with results

        Args:
            practice_id: Notion page ID of practice

        Returns:
            ScoringResult with complete breakdown

        Raises:
            ScoringTimeoutError: If scoring exceeds 5 seconds
            CircuitBreakerError: If circuit breaker is open
            ScoringValidationError: If data validation fails
        """
        start_time = datetime.utcnow()

        try:
            # Enforce 5-second timeout
            async with asyncio.timeout(self.SCORING_TIMEOUT_SECONDS):
                # Fetch scoring input (Google Maps + enrichment)
                scoring_input = await asyncio.to_thread(
                    self.notion_client.fetch_scoring_input,
                    practice_id
                )

                # Calculate score
                scoring_result = await asyncio.to_thread(
                    self.scorer.calculate_score,
                    scoring_input
                )

                # Update Notion
                await asyncio.to_thread(
                    self.notion_client.update_scoring_fields,
                    practice_id,
                    scoring_result
                )

                elapsed = (datetime.utcnow() - start_time).total_seconds()
                self.logger.info(
                    f"Scored practice {practice_id} in {elapsed:.2f}s: "
                    f"{scoring_result.lead_score} pts ({scoring_result.priority_tier.value})"
                )

                return scoring_result

        except asyncio.TimeoutError:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(
                f"Scoring timeout for practice {practice_id} after {elapsed:.2f}s "
                f"(limit: {self.SCORING_TIMEOUT_SECONDS}s)"
            )
            raise ScoringTimeoutError(
                f"Scoring timeout for practice {practice_id} "
                f"(exceeded {self.SCORING_TIMEOUT_SECONDS}s limit)"
            )

        except CircuitBreakerError as e:
            self.logger.error(f"Circuit breaker blocked scoring for {practice_id}: {e}")
            raise

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(
                f"Failed to score practice {practice_id} after {elapsed:.2f}s: {e}",
                exc_info=True
            )
            raise

    def score_practice(self, practice_id: str) -> ScoringResult:
        """
        Score a single practice (synchronous wrapper).

        Args:
            practice_id: Notion page ID of practice

        Returns:
            ScoringResult with complete breakdown

        Raises:
            ScoringTimeoutError: If scoring exceeds 5 seconds
            CircuitBreakerError: If circuit breaker is open
            ScoringValidationError: If data validation fails
        """
        return asyncio.run(self.score_practice_async(practice_id))

    async def score_batch_async(
        self,
        practice_ids: List[str],
        continue_on_error: bool = True
    ) -> Dict[str, any]:
        """
        Score multiple practices with progress tracking.

        Args:
            practice_ids: List of Notion page IDs to score
            continue_on_error: If True, continue scoring after failures

        Returns:
            Dict with results:
            {
                "total": int,
                "succeeded": int,
                "failed": int,
                "timeout": int,
                "circuit_breaker_blocked": int,
                "results": List[ScoringResult],
                "errors": List[Dict[str, str]]
            }
        """
        self.logger.info(f"Starting batch scoring for {len(practice_ids)} practices")

        total = len(practice_ids)
        succeeded = 0
        failed = 0
        timeout_count = 0
        circuit_breaker_blocked = 0
        results = []
        errors = []

        for idx, practice_id in enumerate(practice_ids, 1):
            self.logger.info(f"Scoring practice {idx}/{total}: {practice_id}")

            try:
                result = await self.score_practice_async(practice_id)
                results.append(result)
                succeeded += 1

            except ScoringTimeoutError as e:
                timeout_count += 1
                failed += 1
                errors.append({
                    "practice_id": practice_id,
                    "error_type": "timeout",
                    "error": str(e)
                })
                self.logger.warning(f"Timeout on practice {practice_id}: {e}")

                if not continue_on_error:
                    break

            except CircuitBreakerError as e:
                circuit_breaker_blocked += 1
                failed += 1
                errors.append({
                    "practice_id": practice_id,
                    "error_type": "circuit_breaker",
                    "error": str(e)
                })
                self.logger.error(f"Circuit breaker blocked practice {practice_id}: {e}")

                # Circuit breaker blocks all subsequent requests
                self.logger.error("Circuit breaker open, aborting batch scoring")
                break

            except Exception as e:
                failed += 1
                errors.append({
                    "practice_id": practice_id,
                    "error_type": "general",
                    "error": str(e)
                })
                self.logger.error(f"Error scoring practice {practice_id}: {e}", exc_info=True)

                if not continue_on_error:
                    break

        summary = {
            "total": total,
            "succeeded": succeeded,
            "failed": failed,
            "timeout": timeout_count,
            "circuit_breaker_blocked": circuit_breaker_blocked,
            "results": results,
            "errors": errors
        }

        self.logger.info(
            f"Batch scoring complete: {succeeded}/{total} succeeded, "
            f"{failed} failed (timeouts: {timeout_count}, circuit_breaker: {circuit_breaker_blocked})"
        )

        return summary

    def score_batch(
        self,
        practice_ids: List[str],
        continue_on_error: bool = True
    ) -> Dict[str, any]:
        """
        Score multiple practices (synchronous wrapper).

        Args:
            practice_ids: List of Notion page IDs to score
            continue_on_error: If True, continue scoring after failures

        Returns:
            Dict with results summary
        """
        return asyncio.run(self.score_batch_async(practice_ids, continue_on_error))

    def trigger_scoring_after_enrichment(self, practice_id: str) -> Optional[ScoringResult]:
        """
        Auto-trigger scoring after FEAT-002 enrichment completes.

        This method is called by FEAT-002's EnrichmentOrchestrator when
        enrichment succeeds and auto_trigger_scoring config is enabled.

        Args:
            practice_id: Notion page ID of enriched practice

        Returns:
            ScoringResult if successful, None if failed

        Raises:
            CircuitBreakerError: If circuit breaker is open
        """
        self.logger.info(f"Auto-triggering scoring for enriched practice {practice_id}")

        try:
            result = self.score_practice(practice_id)
            self.logger.info(
                f"Auto-score complete for {practice_id}: "
                f"{result.lead_score} pts ({result.priority_tier.value})"
            )
            return result

        except ScoringTimeoutError as e:
            self.logger.warning(
                f"Auto-score timeout for {practice_id}: {e}. "
                f"Practice can be rescored manually later."
            )
            return None

        except CircuitBreakerError as e:
            self.logger.error(
                f"Auto-score blocked by circuit breaker for {practice_id}: {e}"
            )
            raise

        except Exception as e:
            self.logger.error(
                f"Auto-score failed for {practice_id}: {e}. "
                f"Practice can be rescored manually later.",
                exc_info=True
            )
            return None

    def reset_circuit_breaker(self) -> None:
        """
        Manually reset circuit breaker.

        Used by CLI command to recover from circuit breaker open state.
        """
        self.logger.info("Resetting circuit breaker via orchestrator")
        self.notion_client.reset_circuit_breaker()

    def get_circuit_breaker_status(self) -> Dict[str, any]:
        """
        Get current circuit breaker status.

        Returns:
            Dict with circuit breaker state:
            {
                "open": bool,
                "failures": int,
                "threshold": int,
                "opened_at": Optional[float]
            }
        """
        return {
            "open": self.notion_client.circuit_breaker_open,
            "failures": self.notion_client.circuit_breaker_failures,
            "threshold": self.notion_client.CIRCUIT_BREAKER_THRESHOLD,
            "opened_at": self.notion_client.circuit_breaker_opened_at
        }
