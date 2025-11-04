#!/usr/bin/env python3
"""
FEAT-003: Lead Scoring CLI

Command-line interface for scoring veterinary practice leads.

Usage:
    python score_leads.py --practice-id <page_id>       # Score single practice
    python score_leads.py --batch --all                 # Score all practices
    python score_leads.py --batch --limit 10            # Score first 10 practices
    python score_leads.py --reset-circuit-breaker       # Reset circuit breaker
    python score_leads.py --status                      # Check circuit breaker status

Examples:
    # Score a single practice by Notion page ID
    python score_leads.py --practice-id 2a0edda2-a9a0-81d9-8dc9-daa43c65e744

    # Score all practices in the database
    python score_leads.py --batch --all

    # Score first 50 practices (useful for testing)
    python score_leads.py --batch --limit 50

    # Reset circuit breaker after failures
    python score_leads.py --reset-circuit-breaker

References:
- docs/features/FEAT-003_lead-scoring/prd.md
- docs/features/FEAT-003_lead-scoring/architecture.md
"""

import sys
import time
import logging
from pathlib import Path
from typing import Optional, List

import click
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.config import VetScrapingConfig
from src.utils.logging import setup_logging, get_logger
from src.scoring.lead_scorer import LeadScorer
from src.scoring.scoring_orchestrator import ScoringOrchestrator
from src.integrations.notion_scoring import NotionScoringClient
from src.models.scoring_models import (
    CircuitBreakerError,
    ScoringTimeoutError,
    ScoringValidationError
)

logger = get_logger(__name__)


class ScoringCLIError(Exception):
    """Raised when scoring CLI encounters unrecoverable error."""
    pass


def query_practices_for_scoring(
    notion_client: NotionScoringClient,
    limit: Optional[int] = None
) -> List[str]:
    """
    Query practices from Notion database for scoring.

    Args:
        notion_client: Notion client instance
        limit: Maximum number of practices to return (None = all)

    Returns:
        List of practice page IDs

    Raises:
        ScoringCLIError: If query fails
    """
    try:
        # Query all practices (no filter, we score all)
        response = notion_client.client.databases.query(
            database_id=notion_client.database_id,
            page_size=100 if limit is None else min(limit, 100)
        )

        practice_ids = [page["id"] for page in response.get("results", [])]

        # Handle pagination if needed
        while response.get("has_more") and (limit is None or len(practice_ids) < limit):
            response = notion_client.client.databases.query(
                database_id=notion_client.database_id,
                page_size=100,
                start_cursor=response.get("next_cursor")
            )
            practice_ids.extend([page["id"] for page in response.get("results", [])])

            if limit and len(practice_ids) >= limit:
                practice_ids = practice_ids[:limit]
                break

        logger.info(f"Found {len(practice_ids)} practices for scoring")
        return practice_ids

    except Exception as e:
        logger.error(f"Failed to query practices: {e}", exc_info=True)
        raise ScoringCLIError(f"Failed to query practices: {e}")


@click.command()
@click.option(
    '--practice-id',
    type=str,
    help='Score a single practice by Notion page ID'
)
@click.option(
    '--batch',
    is_flag=True,
    help='Score multiple practices in batch mode'
)
@click.option(
    '--all',
    'score_all',
    is_flag=True,
    help='Score all practices in the database (use with --batch)'
)
@click.option(
    '--limit',
    type=int,
    help='Limit number of practices to score in batch mode'
)
@click.option(
    '--reset-circuit-breaker',
    is_flag=True,
    help='Reset circuit breaker to closed state'
)
@click.option(
    '--status',
    is_flag=True,
    help='Show circuit breaker status'
)
@click.option(
    '--log-level',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False),
    default='INFO',
    help='Logging level (default: INFO)'
)
def main(
    practice_id: Optional[str],
    batch: bool,
    score_all: bool,
    limit: Optional[int],
    reset_circuit_breaker: bool,
    status: bool,
    log_level: str
):
    """FEAT-003: Lead Scoring CLI.

    Score veterinary practice leads based on ICP fit criteria.

    \b
    Modes:
    1. Single practice: --practice-id <page_id>
    2. Batch scoring: --batch --all OR --batch --limit N
    3. Circuit breaker reset: --reset-circuit-breaker
    4. Status check: --status

    \b
    Examples:
        # Score single practice
        python score_leads.py --practice-id 2a0edda2-a9a0-81d9-8dc9-daa43c65e744

        # Score all practices
        python score_leads.py --batch --all

        # Score first 50 practices
        python score_leads.py --batch --limit 50

        # Reset circuit breaker
        python score_leads.py --reset-circuit-breaker
    """
    exit_code = 0

    try:
        # Load configuration
        config = VetScrapingConfig()

        # Setup logging
        setup_logging(log_level=log_level.upper())

        # Validate environment
        if not config.notion.api_key:
            raise ScoringCLIError("Missing NOTION_API_KEY environment variable")
        if not config.notion.database_id:
            raise ScoringCLIError("Missing NOTION_DATABASE_ID environment variable")

        # Initialize components
        notion_client = NotionScoringClient(
            api_key=config.notion.api_key,
            database_id=config.notion.database_id
        )

        scorer = LeadScorer()
        orchestrator = ScoringOrchestrator(
            notion_client=notion_client,
            scorer=scorer
        )

        # Handle different modes
        if reset_circuit_breaker:
            logger.info("Resetting circuit breaker...")
            orchestrator.reset_circuit_breaker()
            click.echo("✓ Circuit breaker reset successfully")
            return

        if status:
            cb_status = orchestrator.get_circuit_breaker_status()
            click.echo("\nCircuit Breaker Status:")
            click.echo(f"  State: {'OPEN (blocking requests)' if cb_status['open'] else 'CLOSED (normal operation)'}")
            click.echo(f"  Failures: {cb_status['failures']}/{cb_status['threshold']}")
            if cb_status['opened_at']:
                elapsed = time.time() - cb_status['opened_at']
                click.echo(f"  Opened: {elapsed:.1f}s ago")
            return

        if practice_id:
            # Single practice mode
            logger.info(f"Scoring single practice: {practice_id}")
            click.echo(f"\nScoring practice {practice_id}...")

            start_time = time.time()
            result = orchestrator.score_practice(practice_id)
            duration = time.time() - start_time

            # Display results
            click.echo(f"\n{'='*60}")
            click.echo("SCORING RESULT")
            click.echo(f"{'='*60}")
            click.echo(f"Practice ID: {practice_id}")
            click.echo(f"Lead Score: {result.lead_score}/120")
            click.echo(f"Priority Tier: {result.priority_tier.value}")
            if result.practice_size_category:
                click.echo(f"Practice Size: {result.practice_size_category.value}")
            click.echo(f"\nComponent Scores:")
            click.echo(f"  Practice Size: {result.score_breakdown.practice_size.score}/{result.score_breakdown.practice_size.max_possible}")
            click.echo(f"  Call Volume: {result.score_breakdown.call_volume.score}/{result.score_breakdown.call_volume.max_possible}")
            click.echo(f"  Technology: {result.score_breakdown.technology.score}/{result.score_breakdown.technology.max_possible}")
            click.echo(f"  Baseline: {result.score_breakdown.baseline.score}/{result.score_breakdown.baseline.max_possible}")
            click.echo(f"  Decision Maker: {result.score_breakdown.decision_maker.score}/{result.score_breakdown.decision_maker.max_possible}")
            click.echo(f"\nConfidence:")
            click.echo(f"  Multiplier: {result.score_breakdown.confidence_multiplier}x")
            click.echo(f"  Total Before: {result.score_breakdown.total_before_confidence}")
            click.echo(f"  Total After: {result.score_breakdown.total_after_confidence}")
            if result.confidence_flags:
                click.echo(f"\nWarnings:")
                for flag in result.confidence_flags:
                    click.echo(f"  ⚠️  {flag}")
            click.echo(f"\nDuration: {duration:.2f}s")
            click.echo(f"{'='*60}\n")

        elif batch:
            # Batch scoring mode
            if not score_all and not limit:
                raise ScoringCLIError("Batch mode requires --all or --limit N")

            logger.info("Starting batch scoring...")
            click.echo("\nQuerying practices...")

            # Query practices
            practice_ids = query_practices_for_scoring(notion_client, limit=limit)

            if not practice_ids:
                click.echo("No practices found for scoring")
                return

            click.echo(f"Found {len(practice_ids)} practices to score\n")

            # Score batch with progress
            start_time = time.time()

            with click.progressbar(
                length=len(practice_ids),
                label='Scoring practices',
                show_eta=True
            ) as bar:
                summary = orchestrator.score_batch(practice_ids, continue_on_error=True)
                bar.update(summary['total'])

            duration = time.time() - start_time

            # Display summary
            click.echo(f"\n{'='*60}")
            click.echo("BATCH SCORING SUMMARY")
            click.echo(f"{'='*60}")
            click.echo(f"Total Practices: {summary['total']}")
            click.echo(f"Succeeded: {summary['succeeded']} ({summary['succeeded']/summary['total']*100:.1f}%)")
            click.echo(f"Failed: {summary['failed']} ({summary['failed']/summary['total']*100:.1f}%)")
            if summary['timeout'] > 0:
                click.echo(f"  Timeouts: {summary['timeout']}")
            if summary['circuit_breaker_blocked'] > 0:
                click.echo(f"  Circuit Breaker: {summary['circuit_breaker_blocked']}")
            click.echo(f"\nDuration: {duration:.1f}s")
            click.echo(f"Average: {duration/summary['total']:.2f}s per practice")

            # Show score distribution
            if summary['results']:
                hot = sum(1 for r in summary['results'] if r.lead_score >= 80)
                warm = sum(1 for r in summary['results'] if 50 <= r.lead_score < 80)
                cold = sum(1 for r in summary['results'] if 20 <= r.lead_score < 50)
                out_of_scope = sum(1 for r in summary['results'] if r.lead_score < 20)

                click.echo(f"\nPriority Distribution:")
                click.echo(f"  🔥 Hot (80-120): {hot}")
                click.echo(f"  🌡️  Warm (50-79): {warm}")
                click.echo(f"  ❄️  Cold (20-49): {cold}")
                click.echo(f"  ⛔ Out of Scope (<20): {out_of_scope}")

            # Show errors if any
            if summary['errors']:
                click.echo(f"\nErrors ({len(summary['errors'])}):")
                for error in summary['errors'][:5]:  # Show first 5
                    click.echo(f"  {error['practice_id']}: {error['error_type']} - {error['error'][:80]}")
                if len(summary['errors']) > 5:
                    click.echo(f"  ... and {len(summary['errors']) - 5} more")

            click.echo(f"{'='*60}\n")

        else:
            # No mode specified
            click.echo("Error: Must specify one of: --practice-id, --batch, --reset-circuit-breaker, or --status")
            click.echo("Use --help for usage information")
            exit_code = 1

    except CircuitBreakerError as e:
        logger.error(f"Circuit breaker blocked scoring: {e}")
        click.echo(f"\n❌ Circuit breaker is OPEN: {e}")
        click.echo("Use --reset-circuit-breaker to manually reset")
        exit_code = 2

    except ScoringTimeoutError as e:
        logger.error(f"Scoring timeout: {e}")
        click.echo(f"\n❌ Scoring timeout: {e}")
        exit_code = 3

    except ScoringValidationError as e:
        logger.error(f"Validation error: {e}")
        click.echo(f"\n❌ Validation error: {e}")
        exit_code = 4

    except ScoringCLIError as e:
        logger.error(f"CLI error: {e}")
        click.echo(f"\n❌ Error: {e}")
        exit_code = 1

    except KeyboardInterrupt:
        logger.warning("Scoring interrupted by user")
        click.echo("\n\n⚠️  Scoring interrupted by user")
        exit_code = 130

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        click.echo(f"\n❌ Unexpected error: {e}")
        click.echo("Check logs for details")
        exit_code = 1

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
