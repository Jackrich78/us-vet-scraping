#!/usr/bin/env python3
"""
FEAT-001: Google Maps → Notion Pipeline CLI

Main entry point for the veterinary practice lead generation pipeline.
Orchestrates scraping, filtering, scoring, and Notion upload with error handling.

Usage:
    python main.py                  # Full run (150 practices)
    python main.py --test           # Test mode (10 practices)
    python main.py --max-results 50 # Custom result limit

References:
- AC-FEAT-001-007: Test mode execution
- AC-FEAT-001-019: Performance (<8 minutes)
- AC-FEAT-001-020: Cost efficiency (<$2)
- AC-FEAT-001-023: Structured logging
"""

import sys
import time
import logging
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

# Load environment variables before importing config
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config.config import VetScrapingConfig
from src.utils.logging import setup_logging
from src.scrapers.apify_client import ApifyClient
from src.processing.data_filter import DataFilter
from src.processing.initial_scorer import InitialScorer
from src.integrations.notion_batch import NotionBatchUpserter
from src.integrations.notion_schema import validate_notion_database, NotionSchemaError

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Raised when pipeline encounters unrecoverable error."""
    pass


def validate_environment(config: VetScrapingConfig) -> None:
    """Validate environment and configuration before pipeline run.

    AC-FEAT-001-018: Missing environment variables.
    AC-FEAT-001-025: Notion database schema validation.

    Args:
        config: Application configuration

    Raises:
        PipelineError: If validation fails
    """
    logger.info("Validating environment configuration...")

    # Validate API keys are set
    try:
        if not config.apify.api_key:
            raise PipelineError("Missing APIFY_API_KEY environment variable")
        if not config.notion.api_key:
            raise PipelineError("Missing NOTION_API_KEY environment variable")
        if not config.notion.database_id:
            raise PipelineError("Missing NOTION_DATABASE_ID environment variable")
    except AttributeError as e:
        raise PipelineError(f"Configuration error: {e}") from e

    # Validate Notion database schema
    try:
        logger.info(f"Validating Notion database schema: {config.notion.database_id}")
        validate_notion_database(
            database_id=config.notion.database_id,
            api_key=config.notion.api_key
        )
        logger.info("✓ Notion database schema validated successfully")
    except NotionSchemaError as e:
        raise PipelineError(f"Notion database validation failed: {e}") from e
    except Exception as e:
        raise PipelineError(f"Failed to connect to Notion: {e}") from e

    logger.info("✓ Environment validation complete")


def run_pipeline(
    config: VetScrapingConfig,
    max_results: int,
    test_mode: bool = False
) -> dict:
    """Execute the complete Google Maps → Notion pipeline.

    Pipeline stages:
    1. Scrape: Apify Google Maps scraper
    2. Filter: Hard filters (website, reviews, open status)
    3. Score: Initial ICP fit scoring (0-25 points)
    4. Upload: Batch upsert to Notion with de-duplication

    Args:
        config: Application configuration
        max_results: Maximum practices to scrape
        test_mode: If True, enable test mode (10 practices, DEBUG logging)

    Returns:
        Dict with pipeline statistics:
        - scraped: Number of practices from Apify
        - filtered: Number after filtering
        - uploaded: Number created in Notion
        - skipped: Number skipped (already exist)
        - failed: Number failed to upload
        - duration_seconds: Total execution time
        - cost_estimate: Estimated cost in USD

    Raises:
        PipelineError: If pipeline fails unrecoverably
    """
    start_time = time.time()

    # Apply test mode settings
    if test_mode:
        config.enable_test_mode()
        max_results = 10
        logger.info("=" * 60)
        logger.info("TEST MODE ENABLED: Limiting to 10 practices")
        logger.info("=" * 60)

    logger.info(f"Starting FEAT-001 pipeline (max_results={max_results})...")

    # ===== Stage 1: Scrape from Google Maps via Apify =====
    logger.info("\n" + "=" * 60)
    logger.info("STAGE 1: Scraping Google Maps via Apify")
    logger.info("=" * 60)

    try:
        apify_client = ApifyClient(
            api_key=config.apify.api_key,
            actor_id=config.apify.actor_id
        )

        # Run actor and get results
        run_id = apify_client.run_google_maps_scraper(
            search_queries=["veterinary clinic in Massachusetts"],
            max_results=max_results,
            location_query="Massachusetts, USA"
        )

        logger.info(f"Apify actor started: run_id={run_id}")

        # Wait for results with timeout
        raw_practices = apify_client.wait_for_results(
            run_id=run_id,
            timeout=config.apify.timeout_seconds
        )

        # Parse and validate results
        practices = apify_client.parse_results(raw_practices)

        logger.info(f"✓ Scraped {len(practices)} practices from Google Maps")

    except Exception as e:
        logger.error(f"Stage 1 failed: {e}", exc_info=True)
        raise PipelineError(f"Scraping failed: {e}") from e

    # AC-FEAT-001-011: Handle empty results
    if not practices:
        logger.warning("No results found from Google Maps scraper")
        return {
            "scraped": 0,
            "filtered": 0,
            "uploaded": 0,
            "skipped": 0,
            "failed": 0,
            "duration_seconds": time.time() - start_time,
            "cost_estimate": 0.0
        }

    # ===== Stage 2: Apply Hard Filters =====
    logger.info("\n" + "=" * 60)
    logger.info("STAGE 2: Applying Hard Filters")
    logger.info("=" * 60)

    try:
        data_filter = DataFilter()

        filtered_practices = data_filter.apply_all_filters(practices, min_reviews=10)

        logger.info(f"✓ Filtered to {len(filtered_practices)} qualifying practices")
        logger.info(f"  Filter pass rate: {len(filtered_practices)/len(practices)*100:.1f}%")

    except Exception as e:
        logger.error(f"Stage 2 failed: {e}", exc_info=True)
        raise PipelineError(f"Filtering failed: {e}") from e

    if not filtered_practices:
        logger.warning("No practices passed filters")
        return {
            "scraped": len(practices),
            "filtered": 0,
            "uploaded": 0,
            "skipped": 0,
            "failed": 0,
            "duration_seconds": time.time() - start_time,
            "cost_estimate": len(practices) * 0.005  # $0.005 per practice
        }

    # ===== Stage 3: Calculate Initial Scores =====
    logger.info("\n" + "=" * 60)
    logger.info("STAGE 3: Calculating Initial ICP Fit Scores")
    logger.info("=" * 60)

    try:
        scorer = InitialScorer()

        scored_practices = scorer.score_batch(filtered_practices)

        # Calculate score distribution
        hot = sum(1 for p in scored_practices if p.priority_tier == "Hot")
        warm = sum(1 for p in scored_practices if p.priority_tier == "Warm")
        cold = sum(1 for p in scored_practices if p.priority_tier == "Cold")

        logger.info(f"✓ Scored {len(scored_practices)} practices")
        logger.info(f"  Score distribution: {hot} Hot, {warm} Warm, {cold} Cold")

    except Exception as e:
        logger.error(f"Stage 3 failed: {e}", exc_info=True)
        raise PipelineError(f"Scoring failed: {e}") from e

    # ===== Stage 4: Batch Upload to Notion =====
    logger.info("\n" + "=" * 60)
    logger.info("STAGE 4: Batch Uploading to Notion")
    logger.info("=" * 60)

    try:
        upserter = NotionBatchUpserter(
            api_key=config.notion.api_key,
            database_id=config.notion.database_id,
            batch_size=config.notion.batch_size,
            rate_limit_delay=config.notion.rate_limit_delay
        )

        upload_result = upserter.upsert_batch(scored_practices)

        logger.info(f"✓ Upload complete:")
        logger.info(f"  Created: {upload_result['created']}")
        logger.info(f"  Skipped: {upload_result['skipped']} (already exist)")
        logger.info(f"  Failed: {upload_result['failed']}")

        if upload_result['failed'] > 0:
            logger.warning(f"  {upload_result['failed']} practices failed to upload:")
            for error in upload_result['errors'][:5]:  # Show first 5 errors
                logger.warning(f"    - {error['place_id']}: {error['error']}")

    except Exception as e:
        logger.error(f"Stage 4 failed: {e}", exc_info=True)
        raise PipelineError(f"Notion upload failed: {e}") from e

    # ===== Pipeline Summary =====
    duration = time.time() - start_time
    cost_estimate = len(practices) * 0.005  # $0.005 per practice from Apify

    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Duration: {duration:.1f}s")
    logger.info(f"Estimated cost: ${cost_estimate:.2f}")
    logger.info(f"Scraped: {len(practices)}")
    logger.info(f"Filtered: {len(filtered_practices)}")
    logger.info(f"Uploaded: {upload_result['created']}")
    logger.info(f"Skipped: {upload_result['skipped']}")
    logger.info(f"Failed: {upload_result['failed']}")

    # AC-FEAT-001-019: Performance validation (<8 minutes)
    if duration > 480 and not test_mode:
        logger.warning(f"⚠ Performance target missed: {duration:.1f}s > 480s (8 min)")

    # AC-FEAT-001-020: Cost validation (<$2)
    if cost_estimate > 2.0 and not test_mode:
        logger.warning(f"⚠ Cost target exceeded: ${cost_estimate:.2f} > $2.00")

    return {
        "scraped": len(practices),
        "filtered": len(filtered_practices),
        "uploaded": upload_result['created'],
        "skipped": upload_result['skipped'],
        "failed": upload_result['failed'],
        "duration_seconds": duration,
        "cost_estimate": cost_estimate
    }


@click.command()
@click.option(
    '--test',
    is_flag=True,
    help='Run in test mode (10 practices, DEBUG logging)'
)
@click.option(
    '--max-results',
    type=int,
    default=150,
    help='Maximum practices to scrape (default: 150)'
)
@click.option(
    '--log-level',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False),
    default='INFO',
    help='Logging level (default: INFO)'
)
def main(test: bool, max_results: int, log_level: str):
    """FEAT-001: Google Maps → Notion Pipeline.

    Scrapes veterinary practices from Google Maps, applies filters,
    calculates initial scores, and uploads to Notion database.

    Examples:

        # Full run (150 practices)
        python main.py

        # Test mode (10 practices, DEBUG logs)
        python main.py --test

        # Custom result limit
        python main.py --max-results 50

    """
    exit_code = 0

    try:
        # Load configuration from environment
        config = VetScrapingConfig()

        # Override log level if specified
        if log_level:
            config.logging.log_level = log_level.upper()

        # Setup logging
        setup_logging(
            log_level=config.logging.log_level,
            log_file=config.logging.log_file if hasattr(config.logging, 'log_file') else None,
            test_mode=test
        )

        logger.info("=" * 60)
        logger.info("FEAT-001: Google Maps → Notion Pipeline")
        logger.info("=" * 60)
        logger.info(f"Version: {config.app_version}")
        logger.info(f"Test mode: {test}")
        logger.info(f"Max results: {max_results if not test else 10}")
        logger.info("=" * 60)

        # Validate environment before running pipeline
        validate_environment(config)

        # Run the pipeline
        result = run_pipeline(
            config=config,
            max_results=max_results,
            test_mode=test
        )

        # Exit with success if no critical failures
        if result['failed'] == 0:
            logger.info("✓ Pipeline completed successfully")
            exit_code = 0
        elif result['uploaded'] > 0:
            logger.warning(f"⚠ Pipeline completed with {result['failed']} failures")
            exit_code = 0  # Partial success
        else:
            logger.error("✗ Pipeline failed: no practices uploaded")
            exit_code = 1

    except PipelineError as e:
        logger.error(f"✗ Pipeline error: {e}")
        exit_code = 1

    except KeyboardInterrupt:
        logger.warning("\n✗ Pipeline interrupted by user (Ctrl+C)")
        exit_code = 130

    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}", exc_info=True)
        exit_code = 1

    finally:
        logger.info("=" * 60)
        logger.info("Pipeline terminated")
        logger.info("=" * 60)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
