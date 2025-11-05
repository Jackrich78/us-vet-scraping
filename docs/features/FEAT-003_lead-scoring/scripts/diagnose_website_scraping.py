#!/usr/bin/env python3
"""
Diagnostic script for website scraping troubleshooting.

Tests a single website URL and shows:
- Which pages Crawl4AI discovers
- Which pages successfully scrape
- HTML content length per page
- Link discovery results
- What the "Invalid URL" errors actually are
- Whether OpenAI can extract missing fields from available content

Usage:
    python diagnose_website_scraping.py <URL>
    python diagnose_website_scraping.py http://www.shelburnefallsvet.com
"""

import asyncio
import sys
import logging
from typing import Dict, List

from src.enrichment.website_scraper import WebsiteScraper
from src.enrichment.llm_extractor import LLMExtractor
from src.utils.cost_tracker import CostTracker
from src.config.config import get_config

# Setup logging (only show INFO and above, suppress DEBUG spam)
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner(text: str, char: str = "="):
    """Print a banner with text."""
    print(f"\n{char * 70}")
    print(f"  {text}")
    print(f"{char * 70}\n")


async def diagnose_website(url: str):
    """Diagnose website scraping for a single URL."""

    print_banner(f"WEBSITE SCRAPING DIAGNOSTIC: {url}")

    config = get_config()

    # Step 1: Test scraping
    print_banner("STEP 1: Website Scraping", "-")
    print(f"Target URL: {url}")
    print(f"Max depth: 1 (homepage + 1 level)")
    print(f"Max pages: 5")
    print(f"URL patterns: *about*, *team*, *staff*, *contact*\n")

    scraper = WebsiteScraper(
        cache_enabled=True,
        max_depth=1,
        max_pages=5,
        page_timeout=30000
    )

    pages = []
    async with scraper:
        pages = await scraper.scrape_multi_page(url)

    print(f"\nRESULTS:")
    print(f"  Total pages scraped: {len(pages)}")

    if not pages:
        print("  ❌ NO PAGES SCRAPED")
        print("\nPossible causes:")
        print("  1. Website is down or unreachable")
        print("  2. Crawl4AI timeout (30s)")
        print("  3. Website blocking automated scrapers")
        print("  4. Invalid URL format")
        print("\nTry manually visiting the URL in a browser to verify it works.")
        return

    # Show page details
    print("\n  Pages discovered:")
    for i, page in enumerate(pages, 1):
        url_lower = page.url.lower()
        page_type = "homepage"
        if "about" in url_lower:
            page_type = "about"
        elif "team" in url_lower or "staff" in url_lower:
            page_type = "team"
        elif "contact" in url_lower:
            page_type = "contact"

        print(f"    {i}. [{page_type:8}] {page.url}")
        print(f"       Title: {page.title or '(none)'}")
        print(f"       Content: {len(page.content):,} characters")

    # Check for missing page types
    page_urls = [p.url.lower() for p in pages]
    missing = []
    if not any("about" in u for u in page_urls):
        missing.append("/about")
    if not any("team" in u or "staff" in u for u in page_urls):
        missing.append("/team or /staff")
    if not any("contact" in u for u in page_urls):
        missing.append("/contact")

    if missing:
        print(f"\n  ⚠️  Missing page types: {', '.join(missing)}")
        print(f"     This may reduce decision maker detection accuracy.")
    else:
        print(f"\n  ✅ All expected page types found!")

    # Step 2: Test extraction
    print_banner("STEP 2: LLM Data Extraction", "-")
    print(f"Using OpenAI GPT-4o with structured outputs\n")

    cost_tracker = CostTracker(budget_limit=10.0)  # $10 budget for diagnostic
    extractor = LLMExtractor(
        cost_tracker=cost_tracker,
        config=config.openai
    )

    try:
        extraction = await extractor.extract_practice_data(
            practice_name="Diagnostic Test Practice",
            website_pages=pages
        )

        print("EXTRACTION RESULTS:")
        print(f"  Vet Count: {extraction.vet_count_total} (confidence: {extraction.vet_count_confidence})")

        if extraction.decision_maker:
            print(f"  Decision Maker:")
            print(f"    Name: {extraction.decision_maker.name or '(not found)'}")
            print(f"    Role: {extraction.decision_maker.role or '(not found)'}")
            print(f"    Email: {extraction.decision_maker.email or '(not found)'}")
            print(f"    Phone: {extraction.decision_maker.phone or '(not found)'}")
        else:
            print(f"  Decision Maker: (not found)")

        # Check the "missing" fields
        print(f"\n  FIELDS ANALYSIS:")

        # Personalization Context
        if extraction.personalization_context:
            print(f"    ✅ Personalization Context: {len(extraction.personalization_context)} items")
            for item in extraction.personalization_context[:3]:
                print(f"       - {item}")
        else:
            print(f"    ❌ Personalization Context: empty")

        # Awards
        if extraction.awards_accreditations:
            print(f"    ✅ Awards/Accreditations: {len(extraction.awards_accreditations)} items")
            for item in extraction.awards_accreditations:
                print(f"       - {item}")
        else:
            print(f"    ❌ Awards/Accreditations: empty (not found on website)")

        # Community Involvement
        if extraction.community_involvement:
            print(f"    ✅ Community Involvement: {len(extraction.community_involvement)} items")
            for item in extraction.community_involvement:
                print(f"       - {item}")
        else:
            print(f"    ❌ Community Involvement: empty (not found on website)")

        # Recent News
        if extraction.recent_news_updates:
            print(f"    ✅ Recent News/Updates: {len(extraction.recent_news_updates)} items")
            for item in extraction.recent_news_updates:
                print(f"       - {item}")
        else:
            print(f"    ❌ Recent News/Updates: empty (not found on website)")

        # Practice Philosophy
        if extraction.practice_philosophy:
            preview = extraction.practice_philosophy[:100]
            print(f"    ✅ Practice Philosophy: {len(extraction.practice_philosophy)} chars")
            print(f"       Preview: {preview}...")
        else:
            print(f"    ❌ Practice Philosophy: empty (not found on website)")

        # Services
        services = []
        if extraction.emergency_24_7:
            services.append("24/7 Emergency")
        if extraction.online_booking:
            services.append("Online Booking")
        if extraction.patient_portal:
            services.append("Patient Portal")
        if extraction.telemedicine_virtual_care:
            services.append("Telemedicine")

        if services:
            print(f"\n  Services Detected: {', '.join(services)}")
        else:
            print(f"\n  Services Detected: None")

        print(f"\n  OpenAI Cost: ${cost_tracker.cumulative_cost:.4f}")

    except Exception as e:
        print(f"  ❌ EXTRACTION FAILED: {e}")
        logger.exception("Extraction error")
        return

    # Step 3: Conclusion
    print_banner("DIAGNOSTIC CONCLUSION", "-")

    if len(pages) >= 3:
        print("✅ SCRAPING PERFORMANCE: GOOD")
        print(f"   {len(pages)} pages scraped (sufficient coverage)")
    elif len(pages) >= 1:
        print("⚠️  SCRAPING PERFORMANCE: PARTIAL")
        print(f"   Only {len(pages)} page(s) scraped (may miss decision maker info)")
    else:
        print("❌ SCRAPING PERFORMANCE: FAILED")
        print("   No pages scraped")

    print()

    # Count populated fields
    populated = 0
    total = 0

    fields_check = [
        ("Vet Count", extraction.vet_count_total is not None),
        ("Decision Maker Name", extraction.decision_maker and extraction.decision_maker.name),
        ("Decision Maker Email", extraction.decision_maker and extraction.decision_maker.email),
        ("24/7 Emergency", extraction.emergency_24_7),
        ("Online Booking", extraction.online_booking),
        ("Patient Portal", extraction.patient_portal),
        ("Telemedicine", extraction.telemedicine_virtual_care),
        ("Awards", bool(extraction.awards_accreditations)),
        ("Community Involvement", bool(extraction.community_involvement)),
        ("Recent News", bool(extraction.recent_news_updates)),
        ("Practice Philosophy", bool(extraction.practice_philosophy)),
    ]

    for field_name, is_populated in fields_check:
        total += 1
        if is_populated:
            populated += 1

    coverage = (populated / total * 100) if total > 0 else 0

    if coverage >= 70:
        print(f"✅ DATA COMPLETENESS: GOOD ({coverage:.0f}%)")
        print(f"   {populated}/{total} key fields populated")
    elif coverage >= 40:
        print(f"⚠️  DATA COMPLETENESS: PARTIAL ({coverage:.0f}%)")
        print(f"   {populated}/{total} key fields populated")
        print(f"   Missing fields likely not on website or in hard-to-find locations")
    else:
        print(f"❌ DATA COMPLETENESS: POOR ({coverage:.0f}%)")
        print(f"   Only {populated}/{total} key fields populated")
        print(f"   Check if website has /about or /team pages with this information")

    print()

    # Recommendations
    print("RECOMMENDATIONS:")

    if missing:
        print(f"  1. Manually check website for: {', '.join(missing)}")
        print(f"     If these pages exist, check URL patterns (they might use different naming)")

    if not extraction.decision_maker or not extraction.decision_maker.email:
        print(f"  2. Decision maker email not found - check /contact, /about, /team pages manually")
        print(f"     Email might be in image format or obfuscated (can't be scraped)")

    if not extraction.awards_accreditations:
        print(f"  3. Awards/Accreditations not found - may not be prominently displayed")

    if not extraction.community_involvement:
        print(f"  4. Community Involvement not found - check /about page or news section")

    print()
    print("=" * 70)


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python diagnose_website_scraping.py <URL>")
        print("\nExample:")
        print("  python diagnose_website_scraping.py http://www.shelburnefallsvet.com")
        sys.exit(1)

    url = sys.argv[1]

    # Validate URL
    if not url.startswith(('http://', 'https://')):
        print(f"Error: Invalid URL format: {url}")
        print("URL must start with http:// or https://")
        sys.exit(1)

    asyncio.run(diagnose_website(url))


if __name__ == "__main__":
    main()
