"""
Multi-page website scraper using Crawl4AI BFSDeepCrawlStrategy.

This module scrapes veterinary practice websites with deep crawling to find
decision maker information on /about, /team, and /staff pages.

Features:
- BFS (Breadth-First Search) multi-page crawling
- URL pattern filtering for targeted pages (*about*, *team*, *staff*, *contact*)
- Concurrent practice processing (5 at once)
- Individual page failure handling (doesn't fail entire practice)
- Cache support for development iteration

Usage:
    scraper = WebsiteScraper(cache_enabled=True)

    async with scraper:
        pages = await scraper.scrape_multi_page("https://example-vet.com")
        print(f"Scraped {len(pages)} pages")
"""

import asyncio
import time
from typing import List, Optional
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

from src.models.enrichment_models import WebsiteData
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WebsiteScraper:
    """Multi-page website scraper using Crawl4AI.

    Scrapes veterinary practice websites using BFS deep crawling with URL
    pattern filtering. Targets homepage + /about + /team + /staff pages
    to maximize decision maker detection.

    Attributes:
        cache_enabled: Enable cache for development (default: True)
        max_depth: Maximum crawl depth (default: 1 = homepage + 1 level)
        max_pages: Maximum pages per practice (default: 5)
        page_timeout: Timeout per page in milliseconds (default: 30000 = 30s)
        url_patterns: URL patterns to match (default: about, team, staff, contact)
    """

    # Default configuration (validated via spike testing)
    DEFAULT_MAX_DEPTH = 1  # Homepage + 1 level
    DEFAULT_MAX_PAGES = 5  # Homepage + up to 4 sub-pages
    DEFAULT_PAGE_TIMEOUT = 30000  # 30 seconds per page
    DEFAULT_URL_PATTERNS = ["*about*", "*team*", "*staff*", "*contact*"]

    def __init__(
        self,
        cache_enabled: bool = True,
        max_depth: int = DEFAULT_MAX_DEPTH,
        max_pages: int = DEFAULT_MAX_PAGES,
        page_timeout: int = DEFAULT_PAGE_TIMEOUT,
        url_patterns: Optional[List[str]] = None
    ):
        """Initialize website scraper.

        Args:
            cache_enabled: Enable cache for development iteration
            max_depth: Maximum crawl depth (1 = homepage + 1 level)
            max_pages: Maximum pages to scrape per practice
            page_timeout: Timeout per page in milliseconds
            url_patterns: URL patterns to match (default: about, team, staff, contact)
        """
        self.cache_enabled = cache_enabled
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.page_timeout = page_timeout
        self.url_patterns = url_patterns or self.DEFAULT_URL_PATTERNS

        self._crawler: Optional[AsyncWebCrawler] = None
        self._config: Optional[CrawlerRunConfig] = None

        logger.info(
            f"WebsiteScraper initialized: max_depth={max_depth}, max_pages={max_pages}, "
            f"patterns={self.url_patterns}, cache={cache_enabled}"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        await self._setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._teardown()

    async def _setup(self):
        """Initialize crawler and configuration."""
        # Configure URL pattern filter
        url_filter = URLPatternFilter(patterns=self.url_patterns)

        # Configure BFS deep crawl strategy
        strategy = BFSDeepCrawlStrategy(
            max_depth=self.max_depth,
            include_external=False,  # Stay within same domain
            max_pages=self.max_pages,
            filter_chain=FilterChain([url_filter])
        )

        # Configure crawler
        self._config = CrawlerRunConfig(
            deep_crawl_strategy=strategy,
            scraping_strategy=LXMLWebScrapingStrategy(),
            cache_mode=CacheMode.ENABLED if self.cache_enabled else CacheMode.BYPASS,
            page_timeout=self.page_timeout,
            verbose=False  # Reduce noise in logs
        )

        # Initialize crawler
        self._crawler = AsyncWebCrawler()
        await self._crawler.__aenter__()

        logger.debug("AsyncWebCrawler initialized and ready")

    async def _teardown(self):
        """Cleanup crawler resources."""
        if self._crawler:
            await self._crawler.__aexit__(None, None, None)
            self._crawler = None
            logger.debug("AsyncWebCrawler closed")

    async def scrape_multi_page(self, url: str) -> List[WebsiteData]:
        """Scrape multiple pages from a practice website.

        Uses BFS deep crawling to find and scrape homepage + /about + /team pages.
        Individual page failures don't fail the entire practice.

        Args:
            url: Practice website URL (e.g., "https://example-vet.com")

        Returns:
            List of WebsiteData objects (one per successfully scraped page)
            Returns empty list if entire site fails or no pages scraped

        Raises:
            RuntimeError: If scraper not initialized (use async context manager)
        """
        if not self._crawler or not self._config:
            raise RuntimeError("WebsiteScraper not initialized. Use 'async with scraper:' context.")

        logger.info(f"Starting multi-page scrape for {url}")
        start_time = time.time()

        try:
            # Run deep crawl
            results = await self._crawler.arun(url, config=self._config)

            elapsed = time.time() - start_time
            success_count = sum(1 for r in results if r.success)

            # Track page types found for better diagnostics
            page_types_found = set()
            failed_pages = []

            logger.info(
                f"Scraped {url}: {len(results)} pages attempted, {success_count} successful "
                f"in {elapsed:.1f}s"
            )

            # Convert results to WebsiteData
            website_pages = []
            for result in results:
                if result.success and result.cleaned_html:
                    # Extract page type from URL for logging
                    url_lower = result.url.lower()
                    page_type = "homepage"
                    if "about" in url_lower:
                        page_type = "about"
                    elif "team" in url_lower or "staff" in url_lower:
                        page_type = "team"
                    elif "contact" in url_lower:
                        page_type = "contact"

                    try:
                        page_data = WebsiteData(
                            url=result.url,
                            title=result.metadata.get("title"),
                            content=result.cleaned_html
                        )
                        website_pages.append(page_data)
                        page_types_found.add(page_type)

                        logger.debug(
                            f"  ✓ {page_type}: {result.url} ({len(result.cleaned_html):,} chars)"
                        )

                    except ValueError as e:
                        # Empty content validation failed - skip this page
                        logger.warning(f"  ✗ {page_type}: {result.url} - empty content")
                        failed_pages.append((page_type, result.url, "empty content"))
                        continue

                elif not result.success:
                    # Log individual page failure but don't fail entire practice
                    url_lower = result.url.lower()
                    page_type = "unknown"
                    if "about" in url_lower:
                        page_type = "about"
                    elif "team" in url_lower or "staff" in url_lower:
                        page_type = "team"
                    elif "contact" in url_lower:
                        page_type = "contact"

                    logger.warning(
                        f"  ✗ Failed to scrape {result.url}: {result.error_message}"
                    )
                    failed_pages.append((page_type, result.url, result.error_message or "unknown error"))

            # Log summary of page coverage
            expected_types = {"homepage", "about", "team", "contact"}
            missing_types = expected_types - page_types_found

            if website_pages:
                logger.info(
                    f"  Page coverage: {', '.join(sorted(page_types_found))} "
                    f"({len(website_pages)} pages)"
                )

                if missing_types:
                    logger.info(
                        f"  Missing pages: {', '.join(sorted(missing_types))} "
                        f"(may impact data completeness)"
                    )

                if failed_pages:
                    logger.warning(f"  Failed {len(failed_pages)} page(s):")
                    for page_type, page_url, error in failed_pages[:3]:  # Show first 3
                        logger.warning(f"    - {page_type}: {error}")
            else:
                logger.warning(f"No pages successfully scraped for {url}")

            return website_pages

        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}", exc_info=True)
            return []  # Return empty list on total failure

    async def scrape_batch(self, urls: List[str], concurrency: int = 5) -> dict:
        """Scrape multiple practice websites concurrently.

        Args:
            urls: List of practice website URLs
            concurrency: Number of concurrent scraping tasks (default: 5)

        Returns:
            Dictionary mapping URL to list of WebsiteData:
            {
                "https://example1.com": [WebsiteData(...), WebsiteData(...)],
                "https://example2.com": [WebsiteData(...)]
            }
        """
        if not self._crawler or not self._config:
            raise RuntimeError("WebsiteScraper not initialized. Use 'async with scraper:' context.")

        logger.info(f"Starting batch scrape: {len(urls)} URLs with concurrency={concurrency}")

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)

        async def scrape_with_semaphore(url: str) -> tuple:
            async with semaphore:
                pages = await self.scrape_multi_page(url)
                return (url, pages)

        # Run all scrapes concurrently (limited by semaphore)
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build result dictionary
        result_dict = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch scrape task failed: {result}")
                continue

            url, pages = result
            result_dict[url] = pages

        successful = sum(1 for pages in result_dict.values() if pages)
        logger.info(
            f"Batch scrape complete: {successful}/{len(urls)} practices "
            f"scraped at least one page"
        )

        return result_dict
