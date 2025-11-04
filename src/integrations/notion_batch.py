"""Notion batch upserter for FEAT-001 Google Maps → Notion pipeline.

Handles batch uploading of practices to Notion with:
- Within-batch de-duplication by Place ID
- Cross-batch de-duplication (skip existing records)
- Rate limiting (3.5s delay between batches)
- Retry logic for 429/5xx errors
- Partial batch failure handling

References:
- AC-FEAT-001-006: Batch Upsert
- AC-FEAT-001-008: Within-batch de-duplication
- AC-FEAT-001-009: Cross-batch de-duplication
- AC-FEAT-001-014: Retry on 429
- AC-FEAT-001-017: Partial batch failure
- AC-FEAT-001-026: Rate limiting
"""

import logging
import time
from typing import List, Set, Dict, Any

from notion_client import Client, APIResponseError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryCallState,
)

from src.models.apify_models import VeterinaryPractice
from src.integrations.notion_mapper import NotionMapper

logger = logging.getLogger(__name__)


def deduplicate_by_place_id(practices: List[VeterinaryPractice]) -> List[VeterinaryPractice]:
    """Remove duplicate practices by Place ID (keep first occurrence).

    AC-FEAT-001-008: De-duplicate within batch.

    Args:
        practices: List of VeterinaryPractice instances (may contain duplicates)

    Returns:
        List of unique practices (first occurrence preserved)

    Example:
        >>> practices = [
        ...     VeterinaryPractice(place_id="ChIJ123", ...),
        ...     VeterinaryPractice(place_id="ChIJ456", ...),
        ...     VeterinaryPractice(place_id="ChIJ123", ...),  # Duplicate
        ... ]
        >>> unique = deduplicate_by_place_id(practices)
        >>> len(unique)  # 2 (duplicate removed)
        2
    """
    seen_ids = set()
    unique_practices = []

    for practice in practices:
        if practice.place_id not in seen_ids:
            unique_practices.append(practice)
            seen_ids.add(practice.place_id)
        else:
            logger.debug(
                f"Skipping duplicate Place ID (within batch): {practice.place_id} "
                f"({practice.practice_name})"
            )

    if len(unique_practices) < len(practices):
        logger.info(
            f"De-duplicated {len(practices) - len(unique_practices)} practices within batch "
            f"({len(unique_practices)} unique)"
        )

    return unique_practices


class NotionBatchUpserter:
    """Batch uploader for veterinary practices to Notion database.

    Handles:
    - De-duplication (within-batch and cross-batch)
    - Batch processing with rate limiting
    - Retry logic for API errors
    - Partial failure recovery

    Example:
        >>> upserter = NotionBatchUpserter(
        ...     api_key="secret_xxx",
        ...     database_id="2a0edda2a9a081d98dc9daa43c65e744",
        ...     batch_size=10,
        ...     rate_limit_delay=3.5
        ... )
        >>>
        >>> practices = [...]  # List of VeterinaryPractice instances
        >>> result = upserter.upsert_batch(practices)
        >>> print(f"Created: {result['created']}, Skipped: {result['skipped']}, Failed: {result['failed']}")
    """

    def __init__(
        self,
        api_key: str,
        database_id: str,
        batch_size: int = 10,
        rate_limit_delay: float = 3.5,
    ):
        """Initialize NotionBatchUpserter.

        Args:
            api_key: Notion integration API key
            database_id: Target Notion database ID
            batch_size: Number of records to process per batch (default: 10)
            rate_limit_delay: Seconds to wait between batches (default: 3.5s = 2.86 req/s)
        """
        self.client = Client(auth=api_key)
        self.database_id = database_id
        self.batch_size = batch_size
        self.rate_limit_delay = rate_limit_delay
        self.mapper = NotionMapper(database_id=database_id)

        logger.info(
            f"NotionBatchUpserter initialized: database={database_id}, "
            f"batch_size={batch_size}, rate_limit_delay={rate_limit_delay}s"
        )

    def check_existing_place_ids(self) -> Set[str]:
        """Query Notion database for all existing Place IDs.

        AC-FEAT-001-009: Check for existing records before uploading.

        Handles pagination (Notion returns max 100 results per page).

        Returns:
            Set of Place IDs already in Notion database

        Example:
            >>> existing_ids = upserter.check_existing_place_ids()
            >>> if "ChIJ123" in existing_ids:
            ...     print("Practice already exists in Notion")
        """
        logger.info("Querying Notion for existing Place IDs...")

        existing_ids = set()
        has_more = True
        start_cursor = None

        while has_more:
            query_params = {"database_id": self.database_id, "page_size": 100}
            if start_cursor:
                query_params["start_cursor"] = start_cursor

            response = self.client.databases.query(**query_params)

            # Extract Place IDs from results
            for result in response.get("results", []):
                try:
                    # Place ID is stored in "Google Place ID" rich_text property
                    place_id_property = result["properties"]["Google Place ID"]
                    place_id = place_id_property["rich_text"][0]["text"]["content"]
                    existing_ids.add(place_id)
                except (KeyError, IndexError) as e:
                    logger.warning(f"Could not extract Place ID from result: {e}")

            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

        logger.info(f"Found {len(existing_ids)} existing Place IDs in Notion database")
        return existing_ids

    def _create_page_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create Notion page with automatic retry on 429/5xx errors only.

        AC-FEAT-001-014: Retry with exponential backoff on 429 errors.
        AC-FEAT-001-015: Retry on 5xx errors.

        Manual retry logic:
        - 5 attempts max
        - Exponential backoff: 1s, 2s, 4s, 8s
        - Only retry on 429 and 5xx errors
        - 400 errors (validation) are NOT retried

        Args:
            payload: Notion page creation payload

        Returns:
            Created page response from Notion API

        Raises:
            APIResponseError: If all retry attempts exhausted or non-retryable error
        """
        max_attempts = 5
        attempt = 0

        while attempt < max_attempts:
            attempt += 1

            try:
                return self.client.pages.create(**payload)

            except APIResponseError as e:
                # Check if it's a retryable error
                should_retry = False
                if hasattr(e, "response") and hasattr(e.response, "status_code"):
                    status_code = e.response.status_code
                    should_retry = status_code == 429 or (500 <= status_code < 600)

                    if status_code == 429:
                        logger.warning(f"Rate limit (429) encountered on attempt {attempt}/{max_attempts}")
                    elif 500 <= status_code < 600:
                        logger.warning(f"Server error ({status_code}) encountered on attempt {attempt}/{max_attempts}")
                    else:
                        # Non-retryable error
                        logger.debug(f"Non-retryable error ({status_code}), not retrying")
                        raise

                if should_retry and attempt < max_attempts:
                    # Exponential backoff: 1s, 2s, 4s, 8s
                    wait_time = min(2 ** (attempt - 1), 8)
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Last attempt or non-retryable
                    raise

        # Should never reach here, but just in case
        raise APIResponseError(
            response=None,
            message="Max retries exhausted",
            code="max_retries"
        )

    def upsert_batch(self, practices: List[VeterinaryPractice]) -> Dict[str, Any]:
        """Batch upsert practices to Notion with de-duplication and error handling.

        Workflow:
        1. De-duplicate within batch (AC-FEAT-001-008)
        2. Query existing Place IDs from Notion (AC-FEAT-001-009)
        3. Filter out existing practices
        4. Process in batches with rate limiting (AC-FEAT-001-006, AC-FEAT-001-026)
        5. Retry on 429/5xx errors (AC-FEAT-001-014, AC-FEAT-001-015)
        6. Handle partial failures gracefully (AC-FEAT-001-017)

        Args:
            practices: List of VeterinaryPractice instances to upload

        Returns:
            Dict with keys:
            - created: Number of pages successfully created
            - skipped: Number of practices skipped (already exist)
            - failed: Number of practices that failed to upload
            - errors: List of error details (place_id, error message)

        Example:
            >>> result = upserter.upsert_batch(practices)
            >>> if result["failed"] > 0:
            ...     for error in result["errors"]:
            ...         print(f"Failed: {error['place_id']} - {error['error']}")
        """
        if not practices:
            logger.info("No practices to upload")
            return {"created": 0, "skipped": 0, "failed": 0, "errors": []}

        logger.info(f"Starting batch upsert for {len(practices)} practices...")

        # Step 1: De-duplicate within batch
        unique_practices = deduplicate_by_place_id(practices)

        # Step 2: Query existing Place IDs
        existing_ids = self.check_existing_place_ids()

        # Step 3: Filter out existing practices
        new_practices = [p for p in unique_practices if p.place_id not in existing_ids]
        skipped_count = len(unique_practices) - len(new_practices)

        if skipped_count > 0:
            logger.info(
                f"Skipping {skipped_count} practices (already exist in Notion)"
            )

        if not new_practices:
            logger.info("No new practices to upload")
            return {"created": 0, "skipped": skipped_count, "failed": 0, "errors": []}

        # Step 4: Process in batches
        created_count = 0
        failed_count = 0
        errors = []

        total_batches = (len(new_practices) + self.batch_size - 1) // self.batch_size

        for batch_num in range(total_batches):
            start_idx = batch_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(new_practices))
            batch = new_practices[start_idx:end_idx]

            logger.info(
                f"Processing batch {batch_num + 1}/{total_batches} "
                f"({len(batch)} practices)..."
            )

            # Process each practice in batch
            for practice in batch:
                try:
                    payload = self.mapper.create_page_payload(practice)
                    self._create_page_with_retry(payload)
                    created_count += 1
                    logger.debug(f"Created page: {practice.place_id} ({practice.practice_name})")

                except APIResponseError as e:
                    # AC-FEAT-001-017: Continue processing despite individual failures
                    failed_count += 1
                    error_detail = {
                        "place_id": practice.place_id,
                        "practice_name": practice.practice_name,
                        "error": str(e),
                    }
                    errors.append(error_detail)
                    logger.error(
                        f"Failed to create page for {practice.place_id} "
                        f"({practice.practice_name}): {e}"
                    )

                except Exception as e:
                    # Catch any unexpected errors
                    failed_count += 1
                    error_detail = {
                        "place_id": practice.place_id,
                        "practice_name": practice.practice_name,
                        "error": f"Unexpected error: {str(e)}",
                    }
                    errors.append(error_detail)
                    logger.error(
                        f"Unexpected error for {practice.place_id}: {e}",
                        exc_info=True
                    )

            # Rate limiting between batches (but not after last batch)
            if batch_num < total_batches - 1:
                logger.debug(f"Rate limiting: sleeping {self.rate_limit_delay}s...")
                time.sleep(self.rate_limit_delay)

        # Summary
        logger.info(
            f"Batch upsert complete: created={created_count}, skipped={skipped_count}, "
            f"failed={failed_count}"
        )

        return {
            "created": created_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "errors": errors,
        }
