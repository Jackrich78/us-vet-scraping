"""
Notion scoring client for FEAT-003 lead scoring.

Handles fetching practice data for scoring and updating scoring fields
while preserving all other fields (enrichment, sales workflow) through partial updates.

Features:
- Fetch Google Maps baseline data (from FEAT-001)
- Fetch enrichment data (from FEAT-002)
- Update scoring fields (lead_score, priority_tier, score_breakdown)
- Batch processing with rate limiting
- Retry logic for API errors
- Circuit breaker pattern for failure isolation

Usage:
    client = NotionScoringClient(api_key=api_key, database_id=database_id)

    # Fetch data for scoring
    google_maps_data = client.fetch_google_maps_data(page_id)
    enrichment_data = client.fetch_enrichment_data(page_id)

    # Update scoring results
    client.update_scoring_fields(page_id, scoring_result)
"""

import logging
import time
from typing import Dict, Optional, List
from datetime import datetime, timezone

from notion_client import Client, APIResponseError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from src.models.scoring_models import ScoringInput, ScoringResult, CircuitBreakerError
from src.models.enrichment_models import VetPracticeExtraction
from src.utils.logging import get_logger

logger = get_logger(__name__)


class NotionScoringClient:
    """Notion client for lead scoring operations.

    Attributes:
        client: Notion SDK client
        database_id: Notion database ID
        rate_limit_delay: Delay between API calls (seconds)
        circuit_breaker_threshold: Consecutive failures before circuit opens
        circuit_breaker_failures: Count of consecutive failures
        circuit_breaker_open: Whether circuit breaker is currently open
    """

    # Notion API rate limit: 3 requests/second
    DEFAULT_RATE_LIMIT_DELAY = 0.35  # 350ms between calls

    # Circuit breaker settings
    CIRCUIT_BREAKER_THRESHOLD = 5  # Open after 5 consecutive failures
    CIRCUIT_BREAKER_COOLDOWN = 60  # 60 seconds before retry

    def __init__(
        self,
        api_key: str,
        database_id: str,
        rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY
    ):
        """Initialize Notion scoring client.

        Args:
            api_key: Notion integration API key
            database_id: Notion database ID (32 chars)
            rate_limit_delay: Delay between API calls in seconds
        """
        self.client = Client(auth=api_key)
        self.database_id = database_id
        self.rate_limit_delay = rate_limit_delay

        # Circuit breaker state
        self.circuit_breaker_failures = 0
        self.circuit_breaker_open = False
        self.circuit_breaker_opened_at: Optional[float] = None

        logger.info(
            f"NotionScoringClient initialized: database={database_id[:8]}..., "
            f"rate_limit={rate_limit_delay}s, circuit_breaker_threshold={self.CIRCUIT_BREAKER_THRESHOLD}"
        )

    def _check_circuit_breaker(self) -> None:
        """Check if circuit breaker should block requests.

        Raises:
            CircuitBreakerError: If circuit is open and cooldown not elapsed
        """
        if not self.circuit_breaker_open:
            return

        # Check if cooldown period has elapsed
        if self.circuit_breaker_opened_at:
            elapsed = time.time() - self.circuit_breaker_opened_at
            if elapsed >= self.CIRCUIT_BREAKER_COOLDOWN:
                logger.info(
                    f"Circuit breaker cooldown elapsed ({elapsed:.1f}s), "
                    f"resetting to closed state"
                )
                self.circuit_breaker_open = False
                self.circuit_breaker_failures = 0
                self.circuit_breaker_opened_at = None
                return

        # Circuit still open
        raise CircuitBreakerError(
            f"Circuit breaker is OPEN after {self.circuit_breaker_failures} consecutive failures. "
            f"Cooldown: {self.CIRCUIT_BREAKER_COOLDOWN}s. "
            f"Blocking scoring attempts to prevent cascading failures."
        )

    def _record_success(self) -> None:
        """Record successful operation, reset circuit breaker."""
        if self.circuit_breaker_failures > 0:
            logger.debug(
                f"Scoring success, resetting circuit breaker "
                f"(was at {self.circuit_breaker_failures} failures)"
            )
        self.circuit_breaker_failures = 0
        self.circuit_breaker_open = False
        self.circuit_breaker_opened_at = None

    def _record_failure(self) -> None:
        """Record failed operation, increment circuit breaker counter."""
        self.circuit_breaker_failures += 1
        logger.warning(
            f"Scoring failure recorded ({self.circuit_breaker_failures}/{self.CIRCUIT_BREAKER_THRESHOLD})"
        )

        if self.circuit_breaker_failures >= self.CIRCUIT_BREAKER_THRESHOLD:
            self.circuit_breaker_open = True
            self.circuit_breaker_opened_at = time.time()
            logger.error(
                f"Circuit breaker OPENED after {self.circuit_breaker_failures} consecutive failures. "
                f"Will block requests for {self.CIRCUIT_BREAKER_COOLDOWN}s."
            )

    def reset_circuit_breaker(self) -> None:
        """Manually reset circuit breaker (for CLI command)."""
        logger.info("Manually resetting circuit breaker")
        self.circuit_breaker_failures = 0
        self.circuit_breaker_open = False
        self.circuit_breaker_opened_at = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(APIResponseError),
        reraise=True
    )
    def fetch_google_maps_data(self, page_id: str) -> Dict:
        """Fetch Google Maps baseline data for a practice.

        Fields fetched:
        - google_rating (Rating field)
        - google_review_count (Review Count field)
        - website (Website field)
        - has_multiple_locations (Multiple Locations field)

        Args:
            page_id: Notion page ID (practice)

        Returns:
            Dict with Google Maps data fields

        Raises:
            APIResponseError: If Notion API call fails
            CircuitBreakerError: If circuit breaker is open
        """
        self._check_circuit_breaker()

        try:
            # Fetch page with Google Maps fields
            response = self.client.pages.retrieve(page_id=page_id)

            properties = response.get("properties", {})

            # Extract Google Maps fields
            google_maps_data = {
                "google_rating": self._extract_number(properties.get("Google Rating")),
                "google_review_count": self._extract_number(properties.get("Google Review Count")),
                "website": self._extract_url(properties.get("Website")),
                "has_multiple_locations": self._extract_checkbox(properties.get("Has Multiple Locations", {}))
            }

            logger.debug(
                f"Fetched Google Maps data for {page_id}: "
                f"rating={google_maps_data['google_rating']}, "
                f"reviews={google_maps_data['google_review_count']}"
            )

            time.sleep(self.rate_limit_delay)
            self._record_success()

            return google_maps_data

        except APIResponseError as e:
            logger.error(f"Failed to fetch Google Maps data for {page_id}: {e}")
            self._record_failure()
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(APIResponseError),
        reraise=True
    )
    def fetch_enrichment_data(self, page_id: str) -> Dict:
        """Fetch enrichment data for a practice.

        Fields fetched:
        - vet_count_total (Vet Count field)
        - vet_count_confidence (Vet Count Confidence field)
        - emergency_24_7 (Emergency 24/7 field)
        - online_booking (Online Booking field)
        - patient_portal (Patient Portal field)
        - telemedicine_virtual_care (Telemedicine field)
        - specialty_services (Specialty Services multi-select field)
        - decision_maker_name (Decision Maker Name field)
        - decision_maker_email (Decision Maker Email field)
        - enrichment_status (Enrichment Status field)

        Args:
            page_id: Notion page ID (practice)

        Returns:
            Dict with enrichment data fields

        Raises:
            APIResponseError: If Notion API call fails
            CircuitBreakerError: If circuit breaker is open
        """
        self._check_circuit_breaker()

        try:
            # Fetch page with enrichment fields
            response = self.client.pages.retrieve(page_id=page_id)

            properties = response.get("properties", {})

            # Extract enrichment fields
            enrichment_data = {
                "vet_count_total": self._extract_number(properties.get("Vet Count")),
                "vet_count_confidence": self._extract_select(properties.get("Vet Count Confidence")),
                "emergency_24_7": self._extract_checkbox(properties.get("24/7 Emergency Services", {})),
                "online_booking": self._extract_checkbox(properties.get("Online Booking", {})),
                "patient_portal": self._extract_checkbox(properties.get("Patient Portal", {})),
                "telemedicine_virtual_care": self._extract_checkbox(properties.get("Telemedicine", {})),
                "specialty_services": self._extract_multi_select(properties.get("Specialty Services", {})),
                "decision_maker_name": self._extract_rich_text(properties.get("Decision Maker Name")),
                "decision_maker_email": self._extract_email(properties.get("Decision Maker Email")),
                "enrichment_status": self._extract_select(properties.get("Enrichment Status"))
            }

            logger.debug(
                f"Fetched enrichment data for {page_id}: "
                f"vet_count={enrichment_data['vet_count_total']}, "
                f"status={enrichment_data['enrichment_status']}"
            )

            time.sleep(self.rate_limit_delay)
            self._record_success()

            return enrichment_data

        except APIResponseError as e:
            logger.error(f"Failed to fetch enrichment data for {page_id}: {e}")
            self._record_failure()
            raise

    def fetch_scoring_input(self, page_id: str) -> ScoringInput:
        """Fetch complete scoring input data (Google Maps + enrichment).

        This is a convenience method that combines fetch_google_maps_data
        and fetch_enrichment_data into a single ScoringInput object.

        Args:
            page_id: Notion page ID (practice)

        Returns:
            ScoringInput with all data needed for scoring

        Raises:
            APIResponseError: If Notion API call fails
            CircuitBreakerError: If circuit breaker is open
        """
        self._check_circuit_breaker()

        try:
            # Fetch both Google Maps and enrichment data
            google_maps_data = self.fetch_google_maps_data(page_id)
            enrichment_data = self.fetch_enrichment_data(page_id)

            # Combine into ScoringInput
            scoring_input = ScoringInput(
                practice_id=page_id,
                # Google Maps data
                google_rating=google_maps_data.get("google_rating"),
                google_review_count=google_maps_data.get("google_review_count"),
                website=google_maps_data.get("website"),
                has_multiple_locations=google_maps_data.get("has_multiple_locations", False),
                # Enrichment data
                vet_count_total=enrichment_data.get("vet_count_total"),
                vet_count_confidence=enrichment_data.get("vet_count_confidence"),
                emergency_24_7=enrichment_data.get("emergency_24_7", False),
                online_booking=enrichment_data.get("online_booking", False),
                patient_portal=enrichment_data.get("patient_portal", False),
                telemedicine_virtual_care=enrichment_data.get("telemedicine_virtual_care", False),
                specialty_services=enrichment_data.get("specialty_services", []),
                decision_maker_name=enrichment_data.get("decision_maker_name"),
                decision_maker_email=enrichment_data.get("decision_maker_email"),
                enrichment_status=enrichment_data.get("enrichment_status")
            )

            logger.info(f"Fetched complete scoring input for {page_id}")
            self._record_success()

            return scoring_input

        except Exception as e:
            logger.error(f"Failed to fetch scoring input for {page_id}: {e}")
            self._record_failure()
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(APIResponseError),
        reraise=True
    )
    def update_scoring_fields(self, page_id: str, scoring_result: ScoringResult) -> None:
        """Update scoring fields in Notion (partial update).

        Updates only scoring fields, preserving all other fields:
        - Lead Score (number)
        - Priority Tier (select)
        - Score Breakdown (rich_text, JSON)
        - Confidence Flags (multi_select)
        - Scoring Status (select)

        Args:
            page_id: Notion page ID (practice)
            scoring_result: Complete scoring result

        Raises:
            APIResponseError: If Notion API call fails
            CircuitBreakerError: If circuit breaker is open
        """
        self._check_circuit_breaker()

        try:
            # Build properties update (partial update, other fields preserved)
            properties = scoring_result.to_notion_update()

            # Update page
            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )

            logger.info(
                f"Updated scoring fields for {page_id}: "
                f"score={scoring_result.lead_score}, tier={scoring_result.priority_tier.value}"
            )

            time.sleep(self.rate_limit_delay)
            self._record_success()

        except APIResponseError as e:
            logger.error(f"Failed to update scoring fields for {page_id}: {e}")
            self._record_failure()
            raise

    # Helper methods for extracting Notion field values

    def _extract_number(self, field: Optional[Dict]) -> Optional[int]:
        """Extract number field value."""
        if not field:
            return None
        return field.get("number")

    def _extract_url(self, field: Optional[Dict]) -> Optional[str]:
        """Extract URL field value."""
        if not field:
            return None
        return field.get("url")

    def _extract_checkbox(self, field: Optional[Dict]) -> bool:
        """Extract checkbox field value."""
        if not field:
            return False
        return field.get("checkbox", False)

    def _extract_select(self, field: Optional[Dict]) -> Optional[str]:
        """Extract select field value."""
        if not field:
            return None
        select = field.get("select")
        if select:
            return select.get("name")
        return None

    def _extract_multi_select(self, field: Optional[Dict]) -> List[str]:
        """Extract multi-select field values."""
        if not field:
            return []
        multi_select = field.get("multi_select", [])
        return [item.get("name") for item in multi_select if item.get("name")]

    def _extract_rich_text(self, field: Optional[Dict]) -> Optional[str]:
        """Extract rich text field value."""
        if not field:
            return None
        rich_text = field.get("rich_text", [])
        if rich_text:
            return rich_text[0].get("plain_text")
        return None

    def _extract_email(self, field: Optional[Dict]) -> Optional[str]:
        """Extract email field value."""
        if not field:
            return None
        return field.get("email")
