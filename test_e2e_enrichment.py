#!/usr/bin/env python3
"""
End-to-End Manual Testing Script for FEAT-002 Website Enrichment

This script allows incremental testing with different practice counts:
- 1 practice: Minimal validation (fastest, cheapest)
- 3 practices: Validate concurrency and variety
- 10 practices: Full test mode validation

Usage:
    # Test with 1 practice (minimal)
    python test_e2e_enrichment.py --limit 1

    # Test with 3 practices
    python test_e2e_enrichment.py --limit 3

    # Test with 10 practices (test mode)
    python test_e2e_enrichment.py --limit 10 --test-mode

    # Full run (150 practices)
    python test_e2e_enrichment.py

Safety Features:
- Dry-run mode to preview without API calls
- Cost estimation before execution
- Confirmation prompts for production runs
- Detailed logging and error reporting
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def print_banner(title: str):
    """Print formatted banner."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def confirm_execution(limit: int, estimated_cost: float, test_mode: bool) -> bool:
    """Ask user to confirm execution.

    Args:
        limit: Number of practices to enrich
        estimated_cost: Estimated total cost
        test_mode: Whether test mode is enabled

    Returns:
        True if user confirms, False otherwise
    """
    print("\n" + "!" * 70)
    print("  EXECUTION CONFIRMATION")
    print("!" * 70)
    print(f"\nYou are about to:")
    print(f"  • Enrich up to {limit} veterinary practices")
    print(f"  • Scrape {limit} websites (multi-page)")
    print(f"  • Make ~{limit} OpenAI API calls")
    print(f"  • Update {limit} Notion records")
    print(f"\nEstimated cost: ${estimated_cost:.4f}")
    print(f"Test mode: {'ENABLED' if test_mode else 'DISABLED'}")
    print("\nThis will make REAL API calls and incur costs.")
    print("!" * 70)

    response = input("\nType 'yes' to proceed, anything else to cancel: ").strip().lower()
    return response == 'yes'


async def dry_run_preview(limit: int):
    """Preview what would be enriched without making API calls.

    Args:
        limit: Number of practices to preview
    """
    print_banner("DRY RUN PREVIEW")

    # Load config manually to avoid Apify requirement
    import os
    from dotenv import load_dotenv
    load_dotenv()

    notion_api_key = os.getenv("NOTION_API_KEY")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_api_key or not notion_database_id:
        print("❌ Missing NOTION_API_KEY or NOTION_DATABASE_ID in .env")
        return None

    # Initialize Notion client only (no API calls to OpenAI/Crawl4AI)
    from src.integrations.notion_enrichment import NotionEnrichmentClient

    notion_client = NotionEnrichmentClient(
        api_key=notion_api_key,
        database_id=notion_database_id
    )

    print(f"Querying Notion for practices needing enrichment (limit={limit})...")
    practices = notion_client.query_practices_for_enrichment(limit=limit)

    print(f"\n✅ Found {len(practices)} practices needing enrichment\n")

    if not practices:
        print("⚠️  No practices found needing enrichment.")
        print("   Either all practices are already enriched, or none have websites.")
        return None

    print("Practices that would be enriched:")
    print("-" * 70)
    for i, practice in enumerate(practices, 1):
        print(f"{i}. {practice['name']}")
        print(f"   Website: {practice['website']}")
        print(f"   ID: {practice['id'][:8]}...")
        print()

    # Estimate cost
    avg_cost_per_practice = 0.000121  # From spike validation
    estimated_total = len(practices) * avg_cost_per_practice * 1.1  # 10% buffer

    print("-" * 70)
    print(f"Estimated cost: ${estimated_total:.4f}")
    print(f"  ({len(practices)} practices × ${avg_cost_per_practice:.6f} per practice × 1.1 buffer)")
    print()

    return {
        "practices": practices,
        "count": len(practices),
        "estimated_cost": estimated_total
    }


async def run_enrichment(limit: int, test_mode: bool, dry_run: bool = False):
    """Run enrichment pipeline.

    Args:
        limit: Maximum number of practices to enrich
        test_mode: Enable test mode (limits to 10)
        dry_run: Preview only, don't execute
    """
    # Dry run preview
    if dry_run:
        await dry_run_preview(limit)
        return

    # Full execution
    print_banner(f"E2E ENRICHMENT TEST - {limit} Practices")

    # Load config
    from src.config.config import get_config
    config = get_config()
    if test_mode:
        config.enable_test_mode()

    # Preview practices
    preview = await dry_run_preview(limit)
    if not preview:
        print("No practices to enrich. Exiting.")
        return

    # Confirm execution
    if not confirm_execution(preview["count"], preview["estimated_cost"], test_mode):
        print("\n❌ Execution cancelled by user.")
        return

    print("\n✅ Confirmed. Starting enrichment pipeline...\n")

    # Initialize orchestrator
    from src.enrichment.enrichment_orchestrator import EnrichmentOrchestrator
    orchestrator = EnrichmentOrchestrator(config=config)

    # Run pipeline
    try:
        results = await orchestrator.enrich_all_practices(
            limit=limit,
            test_mode=test_mode
        )

        # Print detailed results
        print_results(results)

        # Save results to file
        save_results(results, limit)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Partial results may be saved to Notion.")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def print_results(results: dict):
    """Print detailed results.

    Args:
        results: Results dictionary from orchestrator
    """
    print_banner("ENRICHMENT RESULTS")

    total = results["total_queried"]
    successful = results["successful"]
    failed = results["failed"]
    cost = results["cost"]
    elapsed = results["elapsed_time"]

    print(f"Total Practices: {total}")
    print(f"Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"Total Cost: ${cost:.4f}")
    print(f"Elapsed Time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print()

    # Cost per practice
    if successful > 0:
        avg_cost = cost / successful
        print(f"Average cost per successful practice: ${avg_cost:.6f}")
        print()

    # Breakdown by status
    print("Status Breakdown:")
    print("-" * 70)

    status_counts = {}
    for result in results["results"]:
        status = result.status
        status_counts[status] = status_counts.get(status, 0) + 1

    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    print()

    # Failed practices detail
    if failed > 0:
        print("Failed Practices:")
        print("-" * 70)
        for result in results["results"]:
            if result.status != "success":
                print(f"  • {result.practice_name}")
                print(f"    Status: {result.status}")
                print(f"    Error: {result.error_message or 'Unknown'}")
                print()

    # Successful extraction details
    print("Successful Extractions:")
    print("-" * 70)
    for result in results["results"]:
        if result.status == "success" and result.extraction:
            ext = result.extraction
            print(f"  • {result.practice_name}")
            print(f"    Vet Count: {ext.vet_count_total} ({ext.vet_count_confidence})")
            print(f"    Decision Maker: {ext.decision_maker.name if ext.decision_maker else 'None'}")
            print(f"    Email: {ext.decision_maker.email if ext.decision_maker else 'None'}")
            print(f"    Personalization: {len(ext.personalization_context)} facts")
            print(f"    Pages Scraped: {result.pages_scraped}")
            print(f"    Processing Time: {result.processing_time:.1f}s")
            print()


def save_results(results: dict, limit: int):
    """Save results to file.

    Args:
        results: Results dictionary
        limit: Practice limit used
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"enrichment_results_{limit}practices_{timestamp}.txt"
    filepath = Path("data") / "test_results" / filename

    # Create directory if needed
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w") as f:
        f.write(f"FEAT-002 Enrichment Test Results\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Limit: {limit} practices\n")
        f.write(f"=" * 70 + "\n\n")

        f.write(f"Total: {results['total_queried']}\n")
        f.write(f"Successful: {results['successful']}\n")
        f.write(f"Failed: {results['failed']}\n")
        f.write(f"Cost: ${results['cost']:.4f}\n")
        f.write(f"Time: {results['elapsed_time']:.1f}s\n\n")

        f.write("Detailed Results:\n")
        f.write("-" * 70 + "\n")
        for result in results["results"]:
            f.write(f"\n{result.practice_name}\n")
            f.write(f"  Status: {result.status}\n")
            if result.extraction:
                f.write(f"  Vet Count: {result.extraction.vet_count_total}\n")
                f.write(f"  Decision Maker: {result.extraction.decision_maker.name if result.extraction.decision_maker else 'None'}\n")
            if result.error_message:
                f.write(f"  Error: {result.error_message}\n")

    print(f"\n✅ Results saved to: {filepath}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="E2E testing for FEAT-002 website enrichment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run preview (no API calls)
  python test_e2e_enrichment.py --dry-run --limit 10

  # Test with 1 practice (minimal validation)
  python test_e2e_enrichment.py --limit 1

  # Test with 3 practices
  python test_e2e_enrichment.py --limit 3

  # Test with 10 practices (test mode)
  python test_e2e_enrichment.py --limit 10 --test-mode

  # Full production run
  python test_e2e_enrichment.py
        """
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of practices to enrich (default: all)"
    )

    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Enable test mode (limits to 10 practices, DEBUG logging)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview practices without making API calls"
    )

    args = parser.parse_args()

    # Run async
    try:
        asyncio.run(run_enrichment(
            limit=args.limit,
            test_mode=args.test_mode,
            dry_run=args.dry_run
        ))
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
