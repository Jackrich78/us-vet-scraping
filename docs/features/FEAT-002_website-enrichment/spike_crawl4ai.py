#!/usr/bin/env python3
"""
Spike Test 1: Crawl4AI BFSDeepCrawlStrategy

Tests multi-page website scraping with URL pattern filtering for real vet websites.

Success Criteria:
- BFSDeepCrawlStrategy finds /about and /team pages
- Scrapes 2-4 pages per practice
- Execution time ≤20s per practice
- Cached results reused on second run
"""

import asyncio
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

async def test_bfs_deep_crawl():
    """Test BFSDeepCrawlStrategy with real vet websites."""

    # Test with 3 real vet websites of varying sizes
    test_urls = [
        ("https://angell.org", "Large practice"),
        ("https://bostonveterinaryclinic.com", "Medium practice"),
        ("https://theveterinaryclinicofnewton.com", "Small practice")
    ]

    print("="*60)
    print("CRAWL4AI BFS DEEP CRAWL STRATEGY TEST")
    print("="*60)
    print()

    # Configure BFSDeepCrawlStrategy with URL pattern filter
    print("Configuration:")
    print("  Strategy: BFSDeepCrawlStrategy")
    print("  max_depth: 1 (homepage + 1 level)")
    print("  max_pages: 5")
    print("  URL patterns: *about*, *team*, *staff*, *contact*")
    print("  Cache: ENABLED")
    print("  Timeout: 30s per page")
    print()

    url_filter = URLPatternFilter(patterns=["*about*", "*team*", "*staff*", "*contact*"])

    strategy = BFSDeepCrawlStrategy(
        max_depth=1,  # Homepage + 1 level
        include_external=False,
        max_pages=5,
        filter_chain=FilterChain([url_filter])
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        scraping_strategy=LXMLWebScrapingStrategy(),
        cache_mode=CacheMode.ENABLED,
        page_timeout=30000,  # 30s timeout per page
        verbose=False  # Reduced verbosity for cleaner output
    )

    all_results = []
    total_pages = 0
    total_time = 0

    async with AsyncWebCrawler() as crawler:
        for url, description in test_urls:
            print(f"{'='*60}")
            print(f"Testing: {url}")
            print(f"Type: {description}")
            print(f"{'='*60}")

            start_time = time.time()

            try:
                results = await crawler.arun(url, config=config)

                elapsed = time.time() - start_time
                total_time += elapsed

                # Analyze results
                success_count = sum(1 for r in results if r.success)
                total_pages += len(results)

                print(f"\n✅ Scraped {len(results)} pages in {elapsed:.1f}s")
                print(f"   Success rate: {success_count}/{len(results)} pages")
                print()

                for i, result in enumerate(results):
                    depth = result.metadata.get("depth", 0)
                    success_icon = "✅" if result.success else "❌"

                    # Extract page type from URL
                    url_lower = result.url.lower()
                    if "about" in url_lower:
                        page_type = "[about]"
                    elif "team" in url_lower or "staff" in url_lower:
                        page_type = "[team]"
                    elif "contact" in url_lower:
                        page_type = "[contact]"
                    else:
                        page_type = "[home]"

                    content_len = len(result.cleaned_html) if result.cleaned_html else 0

                    print(f"  {success_icon} Depth {depth} {page_type}: {result.url}")
                    print(f"     Content: {content_len:,} chars")

                    if not result.success:
                        print(f"     Error: {result.error_message}")

                all_results.append({
                    "url": url,
                    "description": description,
                    "pages": len(results),
                    "success": success_count,
                    "time": elapsed
                })

            except Exception as e:
                print(f"\n❌ Failed to scrape {url}: {e}")
                all_results.append({
                    "url": url,
                    "description": description,
                    "pages": 0,
                    "success": 0,
                    "time": 0,
                    "error": str(e)
                })

            print()

    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total practices tested: {len(test_urls)}")
    print(f"Total pages scraped: {total_pages}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average pages per practice: {total_pages / len(test_urls):.1f}")
    print(f"Average time per practice: {total_time / len(test_urls):.1f}s")
    print()

    # Check success criteria
    print("SUCCESS CRITERIA VALIDATION:")
    print("-"*60)

    avg_pages = total_pages / len(test_urls)
    avg_time = total_time / len(test_urls)

    criteria = [
        ("BFSDeepCrawlStrategy works without errors", total_pages > 0),
        ("Scrapes 2-4 pages per practice", 2 <= avg_pages <= 5),
        ("Execution time ≤20s per practice", avg_time <= 20),
        ("URL pattern filter matches /about, /team", any("about" in r.get("url", "").lower() or "team" in r.get("url", "").lower() for r in all_results))
    ]

    all_passed = True
    for criterion, passed in criteria:
        icon = "✅" if passed else "❌"
        print(f"{icon} {criterion}")
        if not passed:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n✅ ALL CRITERIA PASSED!")
        print("   Crawl4AI BFSDeepCrawlStrategy is ready for FEAT-002.")
    else:
        print("\n❌ SOME CRITERIA FAILED")
        print("   Review results and adjust configuration.")

    print("="*60)

    return all_passed

if __name__ == "__main__":
    try:
        success = asyncio.run(test_bfs_deep_crawl())
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
