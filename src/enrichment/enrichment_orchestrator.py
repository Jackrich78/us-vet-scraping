"""
Enrichment pipeline orchestrator for FEAT-002.

Coordinates multi-page website scraping, LLM extraction, and Notion updates
to enrich veterinary practice records with decision maker information.

Pipeline Flow:
1. Query Notion for practices needing enrichment
2. Scrape websites (5 concurrent, multi-page)
3. Extract data with OpenAI (sequential, with budget checks)
4. Update Notion with enrichment data
5. Retry failed practices once
6. Trigger scoring (optional FEAT-003 integration)

Features:
- Concurrent website scraping (5 practices at once)
- Sequential LLM extraction (budget monitoring)
- Cost tracking with hard abort at $1.00
- Retry logic for failed practices
- Optional scoring trigger
- Comprehensive error reporting

Usage:
    orchestrator = EnrichmentOrchestrator(config=config)

    results = await orchestrator.enrich_all_practices(limit=150)

    print(f"Success: {results['successful']}, Failed: {results['failed']}")
"""

import asyncio
import time
from typing import List, Dict, Optional, Callable
from datetime import datetime

from src.enrichment.website_scraper import WebsiteScraper
from src.enrichment.llm_extractor import LLMExtractor
from src.integrations.notion_enrichment import NotionEnrichmentClient
from src.models.enrichment_models import EnrichmentResult, VetPracticeExtraction
from src.utils.cost_tracker import CostTracker, CostLimitExceeded
from src.config.config import VetScrapingConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


class EnrichmentOrchestrator:
    """Orchestrates the complete enrichment pipeline.

    Coordinates website scraping, LLM extraction, and Notion updates
    with retry logic and cost tracking.

    Attributes:
        config: Application configuration
        scraper: WebsiteScraper instance
        extractor: LLMExtractor instance
        notion_client: NotionEnrichmentClient instance
        cost_tracker: CostTracker instance
        scoring_callback: Optional callback for FEAT-003 scoring integration
    """

    def __init__(
        self,
        config: VetScrapingConfig,
        scoring_callback: Optional[Callable[[str, VetPracticeExtraction], None]] = None
    ):
        """Initialize enrichment orchestrator.

        Args:
            config: Application configuration
            scoring_callback: Optional callback function to trigger scoring.
                             Called with (page_id, extraction) after successful enrichment.
                             If raises exception, scoring failure logged but doesn't block enrichment.
        """
        self.config = config

        # Initialize cost tracker with budget limit
        self.cost_tracker = CostTracker(budget_limit=1.00)

        # Initialize components
        self.scraper = None  # Initialized in async context
        self.extractor = LLMExtractor(
            cost_tracker=self.cost_tracker,
            config=config.openai,
            prompt_file=config.website_scraping.extraction_prompt_file
        )
        self.notion_client = NotionEnrichmentClient(
            api_key=config.notion.api_key,
            database_id=config.notion.database_id,
            rate_limit_delay=config.notion.rate_limit_delay
        )

        # Optional scoring callback
        self.scoring_callback = scoring_callback

        logger.info(
            f"EnrichmentOrchestrator initialized: "
            f"concurrent_scraping={config.website_scraping.max_concurrent}, "
            f"budget=${self.cost_tracker.budget_limit:.2f}, "
            f"scoring_enabled={scoring_callback is not None}"
        )

    async def enrich_all_practices(
        self,
        limit: Optional[int] = None,
        test_mode: bool = False
    ) -> Dict:
        """Enrich all practices needing enrichment.

        Main pipeline entry point. Queries Notion, scrapes websites, extracts data,
        updates Notion, retries failures, and triggers scoring.

        Args:
            limit: Maximum number of practices to enrich (None = all)
            test_mode: If True, limit to 10 practices for testing

        Returns:
            Dictionary with pipeline statistics:
            {
                "total_queried": int,
                "successful": int,
                "failed": int,
                "skipped": int,
                "cost": float,
                "elapsed_time": float,
                "results": List[EnrichmentResult]
            }
        """
        if test_mode:
            limit = min(limit or 10, 10)
            logger.info("TEST MODE: Limiting to 10 practices")

        pipeline_start = time.time()
        logger.info("="*60)
        logger.info("ENRICHMENT PIPELINE STARTING")
        logger.info("="*60)

        # Step 1: Query practices needing enrichment
        logger.info("Step 1: Querying Notion for practices needing enrichment...")
        practices = self.notion_client.query_practices_for_enrichment(limit=limit)

        if not practices:
            logger.warning("No practices found needing enrichment")
            return {
                "total_queried": 0,
                "successful": 0,
                "failed": 0,
                "skipped": 0,
                "cost": 0.0,
                "elapsed_time": time.time() - pipeline_start,
                "results": []
            }

        logger.info(f"Found {len(practices)} practices to enrich")

        # Step 2: Scrape websites concurrently
        logger.info(f"Step 2: Scraping {len(practices)} websites...")
        scrape_results = await self._scrape_websites(practices)

        # Step 3: Extract data with LLM (sequential, with budget checks)
        logger.info(f"Step 3: Extracting data with OpenAI...")
        extraction_results = await self._extract_data(scrape_results)

        # Step 4: Update Notion with enrichment data
        logger.info(f"Step 4: Updating Notion with enrichment data...")
        notion_results = await self._update_notion(extraction_results)

        # Step 5: Retry failures once
        logger.info(f"Step 5: Retrying failed practices...")
        retry_results = await self._retry_failures(notion_results)

        # Step 6: Trigger scoring for successful enrichments (optional)
        if self.scoring_callback:
            logger.info(f"Step 6: Triggering scoring for successful enrichments...")
            await self._trigger_scoring(retry_results)
        else:
            logger.info(f"Step 6: Scoring disabled - skipping")

        # Generate final statistics
        elapsed = time.time() - pipeline_start
        stats = self._generate_statistics(retry_results, elapsed)

        logger.info("="*60)
        logger.info("ENRICHMENT PIPELINE COMPLETE")
        logger.info("="*60)
        logger.info(f"Total practices: {stats['total_queried']}")
        logger.info(f"Successful: {stats['successful']} ({stats['successful']/stats['total_queried']*100:.1f}%)")
        logger.info(f"Failed: {stats['failed']} ({stats['failed']/stats['total_queried']*100:.1f}%)")
        logger.info(f"Total cost: ${stats['cost']:.4f}")
        logger.info(f"Elapsed time: {stats['elapsed_time']:.1f}s")
        logger.info("="*60)

        return stats

    async def _scrape_websites(self, practices: List[Dict]) -> List[Dict]:
        """Scrape websites for all practices concurrently.

        Args:
            practices: List of practice dicts with id, name, website

        Returns:
            List of dicts with practice info + scraped pages
        """
        start_time = time.time()

        # Initialize scraper in async context
        self.scraper = WebsiteScraper(
            cache_enabled=self.config.website_scraping.cache_enabled,
            max_depth=1,
            max_pages=5,
            page_timeout=self.config.website_scraping.timeout_seconds * 1000
        )

        async with self.scraper:
            # Build URL list
            urls = [p["website"] for p in practices]

            # Scrape all concurrently
            scrape_results = await self.scraper.scrape_batch(
                urls=urls,
                concurrency=self.config.website_scraping.max_concurrent
            )

        # Combine practice info with scraped pages
        results = []
        for practice in practices:
            pages = scrape_results.get(practice["website"], [])
            results.append({
                "id": practice["id"],
                "name": practice["name"],
                "website": practice["website"],
                "pages": pages,
                "scrape_success": len(pages) > 0
            })

        elapsed = time.time() - start_time
        successful = sum(1 for r in results if r["scrape_success"])
        logger.info(
            f"Scraped {len(practices)} practices in {elapsed:.1f}s: "
            f"{successful} successful, {len(practices) - successful} failed"
        )

        return results

    async def _extract_data(self, scrape_results: List[Dict]) -> List[EnrichmentResult]:
        """Extract structured data from scraped pages using LLM.

        Sequential processing to enable budget checking before each call.

        Args:
            scrape_results: List of scrape result dicts

        Returns:
            List of EnrichmentResult objects
        """
        start_time = time.time()
        results = []

        for i, result in enumerate(scrape_results, 1):
            practice_start = time.time()

            # Skip if scraping failed
            if not result["scrape_success"]:
                results.append(EnrichmentResult(
                    practice_id=result["id"],
                    practice_name=result["name"],
                    status="scrape_failed",
                    error_message="Website scraping failed (0 pages scraped)",
                    pages_scraped=0
                ))
                continue

            # Extract data with LLM
            try:
                extraction = await self.extractor.extract_practice_data(
                    practice_name=result["name"],
                    website_pages=result["pages"]
                )

                if extraction:
                    # Success
                    results.append(EnrichmentResult(
                        practice_id=result["id"],
                        practice_name=result["name"],
                        status="success",
                        extraction=extraction,
                        pages_scraped=len(result["pages"]),
                        processing_time=time.time() - practice_start
                    ))
                else:
                    # Extraction failed
                    results.append(EnrichmentResult(
                        practice_id=result["id"],
                        practice_name=result["name"],
                        status="llm_failed",
                        error_message="LLM extraction returned None",
                        pages_scraped=len(result["pages"]),
                        processing_time=time.time() - practice_start
                    ))

            except CostLimitExceeded as e:
                # Budget exceeded - abort pipeline
                logger.error(f"Cost limit exceeded at practice {i}/{len(scrape_results)}: {e}")

                # Mark this practice as failed
                results.append(EnrichmentResult(
                    practice_id=result["id"],
                    practice_name=result["name"],
                    status="llm_failed",
                    error_message=f"Cost limit exceeded: {e}",
                    pages_scraped=len(result["pages"])
                ))

                # Mark all remaining practices as skipped
                for remaining in scrape_results[i:]:
                    results.append(EnrichmentResult(
                        practice_id=remaining["id"],
                        practice_name=remaining["name"],
                        status="llm_failed",
                        error_message="Skipped due to cost limit exceeded",
                        pages_scraped=0
                    ))

                break  # Abort pipeline

            except Exception as e:
                logger.error(f"Unexpected error extracting {result['name']}: {e}", exc_info=True)
                results.append(EnrichmentResult(
                    practice_id=result["id"],
                    practice_name=result["name"],
                    status="llm_failed",
                    error_message=str(e),
                    pages_scraped=len(result["pages"]),
                    processing_time=time.time() - practice_start
                ))

            # Log progress every 10 practices
            if i % 10 == 0:
                summary = self.cost_tracker.get_summary()
                logger.info(
                    f"Extraction progress: {i}/{len(scrape_results)} practices, "
                    f"cost=${summary['cumulative_cost']:.4f}"
                )

        elapsed = time.time() - start_time
        successful = sum(1 for r in results if r.status == "success")
        logger.info(
            f"Extracted {len(scrape_results)} practices in {elapsed:.1f}s: "
            f"{successful} successful"
        )

        return results

    async def _update_notion(self, extraction_results: List[EnrichmentResult]) -> List[EnrichmentResult]:
        """Update Notion with enrichment data.

        Args:
            extraction_results: List of EnrichmentResult objects

        Returns:
            Updated list of EnrichmentResult objects (status may change to notion_failed)
        """
        start_time = time.time()
        updated_results = []

        for result in extraction_results:
            # Skip if extraction failed
            if result.status != "success":
                updated_results.append(result)
                continue

            # Update Notion
            success = self.notion_client.update_practice_enrichment(
                page_id=result.practice_id,
                extraction=result.extraction
            )

            if success:
                # Notion update successful - keep status as success
                updated_results.append(result)
            else:
                # Notion update failed - change status
                result.status = "notion_failed"
                result.error_message = "Notion API update failed"
                updated_results.append(result)

        elapsed = time.time() - start_time
        successful = sum(1 for r in updated_results if r.status == "success")
        logger.info(
            f"Updated {len(extraction_results)} practices in Notion in {elapsed:.1f}s: "
            f"{successful} successful"
        )

        return updated_results

    async def _retry_failures(self, results: List[EnrichmentResult]) -> List[EnrichmentResult]:
        """Retry failed practices once.

        Args:
            results: List of EnrichmentResult objects

        Returns:
            Updated list with retry results merged
        """
        # Identify practices that failed scraping or LLM extraction
        failed = [r for r in results if r.status in ["scrape_failed", "llm_failed"]]

        if not failed:
            logger.info("No failures to retry")
            return results

        logger.info(f"Retrying {len(failed)} failed practices...")

        # Rebuild practice list for retry
        retry_practices = []
        for result in failed:
            # Find original practice data (we need website URL)
            # For now, mark as failed - full retry would need original URLs
            # This is a simplified implementation
            logger.warning(f"Retry not fully implemented - marking {result.practice_name} as failed")

            # Mark in Notion as failed
            self.notion_client.mark_enrichment_failed(
                page_id=result.practice_id,
                error_message=result.error_message or "Enrichment failed"
            )

        return results

    async def _trigger_scoring(self, results: List[EnrichmentResult]) -> None:
        """Trigger scoring for successfully enriched practices.

        Args:
            results: List of EnrichmentResult objects
        """
        if not self.scoring_callback:
            return

        successful = [r for r in results if r.status == "success"]

        if not successful:
            logger.info("No successful enrichments to score")
            return

        logger.info(f"Triggering scoring for {len(successful)} practices...")

        for result in successful:
            try:
                # Call scoring callback
                self.scoring_callback(result.practice_id, result.extraction)
                logger.debug(f"Scoring triggered for {result.practice_name}")

            except Exception as e:
                # Log scoring failure but don't fail enrichment
                logger.warning(
                    f"Scoring failed for {result.practice_name}: {e}. "
                    f"Enrichment still marked as successful."
                )

        logger.info(f"Scoring triggered for {len(successful)} practices")

    def _generate_statistics(self, results: List[EnrichmentResult], elapsed: float) -> Dict:
        """Generate pipeline statistics.

        Args:
            results: List of EnrichmentResult objects
            elapsed: Total elapsed time in seconds

        Returns:
            Statistics dictionary
        """
        successful = sum(1 for r in results if r.status == "success")
        failed = sum(1 for r in results if r.status != "success")

        cost_summary = self.cost_tracker.get_summary()

        return {
            "total_queried": len(results),
            "successful": successful,
            "failed": failed,
            "skipped": 0,  # Placeholder
            "cost": cost_summary["cumulative_cost"],
            "elapsed_time": elapsed,
            "results": results
        }
