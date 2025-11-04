"""
Notion enrichment client for FEAT-002 website enrichment.

Handles querying practices for enrichment and updating enrichment fields
while preserving sales workflow fields through partial updates.

Features:
- Query practices needing enrichment (new OR stale >30 days)
- Partial updates (enrichment fields only, sales fields preserved automatically)
- Batch processing with rate limiting
- Retry logic for API errors

Usage:
    client = NotionEnrichmentClient(api_key=api_key, database_id=database_id)

    # Query practices needing enrichment
    practices = client.query_practices_for_enrichment()

    # Update practice with enrichment data
    client.update_practice_enrichment(
        page_id=practice_id,
        extraction=vet_practice_extraction
    )
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta

from notion_client import Client, APIResponseError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from src.models.enrichment_models import VetPracticeExtraction
from src.utils.logging import get_logger

logger = get_logger(__name__)


class NotionEnrichmentClient:
    """Notion client for website enrichment operations.

    Attributes:
        client: Notion SDK client
        database_id: Notion database ID
        rate_limit_delay: Delay between API calls (seconds)
    """

    # Notion API rate limit: 3 requests/second
    DEFAULT_RATE_LIMIT_DELAY = 0.35  # 350ms between calls

    def __init__(
        self,
        api_key: str,
        database_id: str,
        rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY
    ):
        """Initialize Notion enrichment client.

        Args:
            api_key: Notion integration API key
            database_id: Notion database ID (32 chars)
            rate_limit_delay: Delay between API calls in seconds
        """
        self.client = Client(auth=api_key)
        self.database_id = database_id
        self.rate_limit_delay = rate_limit_delay

        logger.info(
            f"NotionEnrichmentClient initialized: database={database_id[:8]}..., "
            f"rate_limit={rate_limit_delay}s"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(APIResponseError),
        reraise=True
    )
    def query_practices_for_enrichment(
        self,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Query practices needing enrichment.

        Returns practices where:
        - Enrichment Status != "Completed" (never enriched)
        OR
        - Last Enrichment Date > 30 days ago (stale, needs re-enrichment)

        Args:
            limit: Maximum number of practices to return (None = all)

        Returns:
            List of practice dictionaries with id, name, website URL
            [
                {
                    "id": "page_id",
                    "name": "Practice Name",
                    "website": "https://example.com"
                },
                ...
            ]
        """
        logger.info("Querying practices for enrichment...")

        # Calculate 30 days ago for stale enrichment filter
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

        # Build OR filter: not completed OR stale
        filter_query = {
            "or": [
                {
                    "property": "Enrichment Status",
                    "select": {
                        "does_not_equal": "Completed"
                    }
                },
                {
                    "property": "Last Enrichment Date",
                    "date": {
                        "before": thirty_days_ago
                    }
                }
            ]
        }

        # Query with filter
        try:
            results = []
            has_more = True
            start_cursor = None

            while has_more:
                query_params = {
                    "database_id": self.database_id,
                    "filter": filter_query
                }

                if start_cursor:
                    query_params["start_cursor"] = start_cursor

                if limit and len(results) >= limit:
                    break

                response = self.client.databases.query(**query_params)

                # Extract practice data
                for page in response["results"]:
                    # Get practice name
                    name_prop = page["properties"].get("Practice Name", {})
                    name = ""
                    if name_prop.get("title"):
                        name = name_prop["title"][0].get("plain_text", "")

                    # Get website URL
                    website_prop = page["properties"].get("Website", {})
                    website = website_prop.get("url")

                    # Skip if no website (can't enrich without website)
                    if not website:
                        logger.debug(f"Skipping {name}: no website URL")
                        continue

                    results.append({
                        "id": page["id"],
                        "name": name,
                        "website": website
                    })

                    if limit and len(results) >= limit:
                        has_more = False
                        break

                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")

            logger.info(f"Found {len(results)} practices needing enrichment")
            return results

        except APIResponseError as e:
            logger.error(f"Notion API error querying practices: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error querying practices: {e}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(APIResponseError),
        reraise=True
    )
    def update_practice_enrichment(
        self,
        page_id: str,
        extraction: VetPracticeExtraction
    ) -> bool:
        """Update practice with enrichment data.

        Uses partial update - only enrichment fields updated, sales workflow
        fields automatically preserved by Notion API.

        Args:
            page_id: Notion page ID
            extraction: Extracted data from website

        Returns:
            True if successful, False otherwise
        """
        logger.debug(f"Updating enrichment for page {page_id[:8]}...")

        # Build enrichment field updates (only fields that have data)
        properties = {}

        # Vet count
        if extraction.vet_count_total is not None:
            properties["Confirmed Vet Count (Total)"] = {"number": extraction.vet_count_total}

        if extraction.vet_count_confidence:
            properties["Vet Count Confidence"] = {
                "select": {"name": extraction.vet_count_confidence}
            }

        # Decision maker
        if extraction.decision_maker:
            if extraction.decision_maker.name:
                properties["Decision Maker Name"] = {
                    "rich_text": [{"text": {"content": extraction.decision_maker.name}}]
                }

            if extraction.decision_maker.role:
                properties["Decision Maker Role"] = {
                    "select": {"name": extraction.decision_maker.role}
                }

            if extraction.decision_maker.email:
                properties["Decision Maker Email"] = {
                    "email": extraction.decision_maker.email
                }

            if extraction.decision_maker.phone:
                properties["Decision Maker Phone"] = {
                    "phone_number": extraction.decision_maker.phone
                }

        # Technology indicators
        properties["24/7 Emergency Services"] = {"checkbox": extraction.emergency_24_7}
        properties["Online Booking"] = {"checkbox": extraction.online_booking}
        properties["Patient Portal"] = {"checkbox": extraction.patient_portal}
        properties["Telemedicine"] = {"checkbox": extraction.telemedicine_virtual_care}

        # Specialty services
        if extraction.specialty_services:
            properties["Specialty Services"] = {
                "multi_select": [{"name": service} for service in extraction.specialty_services[:10]]
            }

        # Personalization context (store as rich_text, line-separated)
        if extraction.personalization_context:
            context_text = "\n".join(extraction.personalization_context)
            properties["Personalization Context"] = {
                "rich_text": [{"text": {"content": context_text}}]
            }

        # Awards and accreditations
        if extraction.awards_accreditations:
            properties["Awards/Accreditations"] = {
                "multi_select": [{"name": award} for award in extraction.awards_accreditations[:5]]
            }

        # Recent news
        if extraction.recent_news_updates:
            news_text = "\n".join(extraction.recent_news_updates)
            properties["Recent News/Updates"] = {
                "rich_text": [{"text": {"content": news_text}}]
            }

        # Community involvement
        if extraction.community_involvement:
            community_text = "\n".join(extraction.community_involvement)
            properties["Community Involvement"] = {
                "rich_text": [{"text": {"content": community_text}}]
            }

        # Practice philosophy
        if extraction.practice_philosophy:
            properties["Practice Philosophy/Mission"] = {
                "rich_text": [{"text": {"content": extraction.practice_philosophy}}]
            }

        # Enrichment status and timestamp
        properties["Enrichment Status"] = {"select": {"name": "Completed"}}
        properties["Last Enrichment Date"] = {
            "date": {"start": datetime.now(timezone.utc).isoformat()}
        }

        # Update page with partial update (sales fields preserved automatically)
        try:
            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )

            logger.debug(f"Successfully updated page {page_id[:8]}")
            return True

        except APIResponseError as e:
            logger.error(f"Notion API error updating page {page_id[:8]}: {e}")
            return False

        except Exception as e:
            logger.error(
                f"Unexpected error updating page {page_id[:8]}: {e}",
                exc_info=True
            )
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(APIResponseError),
        reraise=True
    )
    def mark_enrichment_failed(
        self,
        page_id: str,
        error_message: str
    ) -> bool:
        """Mark practice enrichment as failed with error message.

        Args:
            page_id: Notion page ID
            error_message: Error description

        Returns:
            True if successful, False otherwise
        """
        logger.debug(f"Marking page {page_id[:8]} as enrichment failed...")

        properties = {
            "Enrichment Status": {"select": {"name": "Failed"}},
            "Enrichment Error": {
                "rich_text": [{"text": {"content": error_message[:2000]}}]  # Truncate to 2000 chars
            },
            "Last Enrichment Date": {
                "date": {"start": datetime.now(timezone.utc).isoformat()}
            }
        }

        try:
            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )

            logger.debug(f"Successfully marked page {page_id[:8]} as failed")
            return True

        except Exception as e:
            logger.error(
                f"Failed to mark page {page_id[:8]} as failed: {e}",
                exc_info=True
            )
            return False
