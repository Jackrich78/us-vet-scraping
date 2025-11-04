#!/usr/bin/env python3
"""
Quick validation test for FEAT-002 enrichment pipeline.

Tests basic imports and initialization of all components.
Does NOT make actual API calls (use spike tests for that).

Usage:
    python test_enrichment_pipeline.py
"""

import sys
import asyncio
from pathlib import Path


def test_imports():
    """Test that all modules import correctly."""
    print("Testing imports...")
    print("-" * 60)

    try:
        # Phase 1: Models and utilities
        from src.models.enrichment_models import (
            VetPracticeExtraction,
            DecisionMaker,
            WebsiteData,
            EnrichmentResult
        )
        print("✅ enrichment_models imported")

        from src.utils.cost_tracker import CostTracker, CostLimitExceeded
        print("✅ cost_tracker imported")

        # Phase 2: Website scraper
        from src.enrichment.website_scraper import WebsiteScraper
        print("✅ website_scraper imported")

        # Phase 3: LLM extractor
        from src.enrichment.llm_extractor import LLMExtractor
        print("✅ llm_extractor imported")

        # Phase 4: Notion client
        from src.integrations.notion_enrichment import NotionEnrichmentClient
        print("✅ notion_enrichment imported")

        # Phase 5: Orchestrator
        from src.enrichment.enrichment_orchestrator import EnrichmentOrchestrator
        print("✅ enrichment_orchestrator imported")

        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_validation():
    """Test Pydantic model validation."""
    print("\nTesting Pydantic model validation...")
    print("-" * 60)

    try:
        from src.models.enrichment_models import (
            VetPracticeExtraction,
            DecisionMaker,
            WebsiteData
        )
        from datetime import datetime

        # Test DecisionMaker
        dm = DecisionMaker(
            name="Dr. Test",
            role="Owner",
            email="test@example.com",
            phone="555-1234"
        )
        print(f"✅ DecisionMaker created: {dm.name}")

        # Test VetPracticeExtraction
        extraction = VetPracticeExtraction(
            vet_count_total=3,
            vet_count_confidence="high",
            decision_maker=dm,
            emergency_24_7=True,
            online_booking=True,
            personalization_context=["Test fact 1", "Test fact 2"]
        )
        print(f"✅ VetPracticeExtraction created: {extraction.vet_count_total} vets")

        # Test WebsiteData
        page = WebsiteData(
            url="https://example.com",
            title="Test Page",
            content="Sample content"
        )
        print(f"✅ WebsiteData created: {page.url}")

        return True

    except Exception as e:
        print(f"❌ Model validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cost_tracker():
    """Test CostTracker functionality."""
    print("\nTesting CostTracker...")
    print("-" * 60)

    try:
        from src.utils.cost_tracker import CostTracker, CostLimitExceeded

        # Create tracker with $1 budget
        tracker = CostTracker(budget_limit=1.00)
        print(f"✅ CostTracker created with ${tracker.budget_limit:.2f} budget")

        # Test token counting
        tokens = tracker.count_tokens("This is a test sentence for token counting.")
        print(f"✅ Token counting works: {tokens} tokens")

        # Test cost estimation
        cost = tracker.estimate_cost("Short test text", estimated_output_tokens=100)
        print(f"✅ Cost estimation works: ${cost:.6f}")

        # Test budget check (should pass)
        tracker.check_budget("Short test", estimated_output_tokens=100)
        print(f"✅ Budget check passed")

        # Test actual cost tracking
        call_cost = tracker.track_call(input_tokens=50, output_tokens=30)
        print(f"✅ Cost tracking works: ${call_cost:.6f}")

        # Test summary
        summary = tracker.get_summary()
        print(f"✅ Summary: {summary['call_count']} calls, ${summary['cumulative_cost']:.6f} spent")

        return True

    except Exception as e:
        print(f"❌ CostTracker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_component_initialization():
    """Test that components initialize without errors."""
    print("\nTesting component initialization...")
    print("-" * 60)

    try:
        from src.config.config import VetScrapingConfig
        from src.utils.cost_tracker import CostTracker

        # Load config (requires .env file)
        try:
            config = VetScrapingConfig()
            print("✅ Config loaded from .env")
        except Exception as e:
            print(f"⚠️  Config loading failed (expected if .env missing): {e}")
            print("   Skipping component initialization tests")
            return True

        # Test CostTracker initialization
        tracker = CostTracker(budget_limit=1.00)
        print("✅ CostTracker initialized")

        # Test LLM extractor initialization (requires prompt file)
        from src.enrichment.llm_extractor import LLMExtractor
        try:
            extractor = LLMExtractor(
                cost_tracker=tracker,
                config=config.openai,
                prompt_file="config/website_extraction_prompt.txt"
            )
            print("✅ LLMExtractor initialized")
        except FileNotFoundError:
            print("⚠️  LLMExtractor initialization failed (prompt file not found)")

        # Test Notion client initialization
        from src.integrations.notion_enrichment import NotionEnrichmentClient
        notion_client = NotionEnrichmentClient(
            api_key=config.notion.api_key,
            database_id=config.notion.database_id
        )
        print("✅ NotionEnrichmentClient initialized")

        return True

    except Exception as e:
        print(f"❌ Component initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_webscraper_init():
    """Test WebsiteScraper initialization."""
    print("\nTesting WebsiteScraper initialization...")
    print("-" * 60)

    try:
        from src.enrichment.website_scraper import WebsiteScraper

        scraper = WebsiteScraper(
            cache_enabled=True,
            max_depth=1,
            max_pages=5
        )
        print("✅ WebsiteScraper created")

        # Test async context manager setup
        async with scraper:
            print("✅ WebsiteScraper async context manager works")

        return True

    except Exception as e:
        print(f"❌ WebsiteScraper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("FEAT-002 ENRICHMENT PIPELINE VALIDATION")
    print("=" * 60)
    print()

    results = []

    # Test 1: Imports
    results.append(("Imports", test_imports()))

    # Test 2: Model validation
    results.append(("Model Validation", test_model_validation()))

    # Test 3: CostTracker
    results.append(("CostTracker", test_cost_tracker()))

    # Test 4: Component initialization
    results.append(("Component Initialization", test_component_initialization()))

    # Test 5: WebsiteScraper (async)
    scraper_result = asyncio.run(test_webscraper_init())
    results.append(("WebsiteScraper", scraper_result))

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        icon = "✅" if result else "❌"
        print(f"{icon} {test_name}")

    print("-" * 60)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL VALIDATION TESTS PASSED!")
        print("   FEAT-002 implementation is ready for integration testing.")
        return 0
    else:
        print(f"\n❌ {total - passed} TESTS FAILED")
        print("   Review errors above and fix issues.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
