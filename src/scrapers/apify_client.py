"""
Apify Client for Google Maps scraping (FEAT-001).

Wrapper around Apify API to run compass/crawler-google-places actor
with retry logic, timeout handling, and Pydantic validation.
"""

import time
import logging
from typing import List, Dict, Any
from apify_client import ApifyClient as ApifySDK
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.models.apify_models import ApifyGoogleMapsResult

logger = logging.getLogger(__name__)


class ApifyClient:
    """
    Client for Apify Google Maps scraping.

    Handles:
    - Actor execution with retry logic
    - Status polling with timeout
    - Result parsing into Pydantic models
    - Error handling and logging
    """

    def __init__(self, api_key: str, actor_id: str = "compass/crawler-google-places"):
        """
        Initialize Apify client.

        Args:
            api_key: Apify API key (apify_api_*)
            actor_id: Apify actor ID (default: compass/crawler-google-places)

        Raises:
            ValueError: If API key is empty or invalid
        """
        if not api_key or not isinstance(api_key, str) or len(api_key) < 10:
            raise ValueError(
                "Invalid Apify API key. "
                "Provide a valid API key starting with 'apify_api_'"
            )

        self.api_key = api_key
        self.actor_id = actor_id
        self._client = None

    def _get_apify_client(self) -> ApifySDK:
        """Lazy initialization of Apify SDK client."""
        if self._client is None:
            self._client = ApifySDK(self.api_key)
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=5, max=120),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def run_google_maps_scraper(
        self,
        search_queries: List[str],
        max_results: int = 50,
        location_query: str = "Massachusetts, USA",
    ) -> str:
        """
        Trigger Apify Google Maps actor run (AC-FEAT-001-001, AC-FEAT-001-012).

        Args:
            search_queries: List of search strings (e.g., ["veterinary clinic in Boston, MA"])
            max_results: Max places per search (default: 50)
            location_query: Location filter (default: Massachusetts, USA)

        Returns:
            run_id: Apify run ID for status polling

        Raises:
            Exception: If actor call fails after retries
        """
        client = self._get_apify_client()

        # Construct actor input per AC-FEAT-001-024
        actor_input = {
            "searchStringsArray": search_queries,
            "locationQuery": location_query,
            "maxCrawledPlacesPerSearch": max_results,
            "language": "en",
            "includeReviews": False,  # Don't need full review text
            "includeImages": False,  # Don't need images
            "includeOpeningHours": True,  # Need for open status filter
        }

        logger.info(
            f"Triggering Apify actor {self.actor_id}",
            extra={
                "search_queries": search_queries,
                "max_results": max_results,
                "location": location_query,
            },
        )

        # Call actor (with retry decorator)
        run_info = client.actor(self.actor_id).call(run_input=actor_input)

        run_id = run_info["id"]
        logger.info(f"Actor run started: {run_id}")

        return run_id

    def wait_for_results(
        self, run_id: str, timeout: int = 600, poll_interval: int = 10
    ) -> str:
        """
        Wait for actor run to complete (AC-FEAT-001-001, AC-FEAT-001-013).

        Args:
            run_id: Apify run ID from run_google_maps_scraper()
            timeout: Max wait time in seconds (default: 600)
            poll_interval: Seconds between status checks (default: 10)

        Returns:
            dataset_id: Dataset ID containing scraped results

        Raises:
            TimeoutError: If run doesn't complete within timeout
        """
        client = self._get_apify_client()
        start_time = time.time()

        logger.info(f"Waiting for actor run {run_id} to complete (timeout: {timeout}s)")

        while True:
            elapsed = time.time() - start_time

            if elapsed > timeout:
                raise TimeoutError(
                    f"Actor run {run_id} did not complete within {timeout} seconds"
                )

            # Check run status
            run_info = client.run(run_id).get()
            status = run_info["status"]

            logger.debug(
                f"Actor run status: {status}",
                extra={"run_id": run_id, "elapsed_seconds": int(elapsed)},
            )

            if status == "SUCCEEDED":
                dataset_id = run_info["defaultDatasetId"]
                logger.info(
                    f"Actor run completed successfully: {run_id}",
                    extra={"dataset_id": dataset_id},
                )
                return dataset_id

            elif status == "FAILED":
                raise RuntimeError(f"Actor run {run_id} failed")

            elif status == "ABORTED":
                raise RuntimeError(f"Actor run {run_id} was aborted")

            # Still running, wait before next poll
            time.sleep(poll_interval)

    def parse_results(self, dataset_id: str) -> List[ApifyGoogleMapsResult]:
        """
        Parse Apify dataset into validated Pydantic models (AC-FEAT-001-001, AC-FEAT-001-016).

        Args:
            dataset_id: Apify dataset ID from wait_for_results()

        Returns:
            List of ApifyGoogleMapsResult Pydantic models

        Raises:
            ValidationError: If any record fails validation
        """
        client = self._get_apify_client()

        logger.info(f"Parsing Apify dataset: {dataset_id}")

        results = []
        for item in client.dataset(dataset_id).iterate_items():
            # Validate with Pydantic model
            result = ApifyGoogleMapsResult(**item)
            results.append(result)

        logger.info(
            f"Parsed {len(results)} practices from Apify",
            extra={"dataset_id": dataset_id, "count": len(results)},
        )

        return results
