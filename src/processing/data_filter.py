"""
Data filtering for veterinary practices (FEAT-001).

Applies quality filters to exclude:
- Practices without websites (AC-FEAT-001-002)
- Practices with <10 reviews (AC-FEAT-001-003)
- Permanently closed practices (AC-FEAT-001-004)
"""

import logging
from typing import List
from src.models.apify_models import ApifyGoogleMapsResult

logger = logging.getLogger(__name__)


class DataFilter:
    """
    Filter service for veterinary practice data quality.

    Provides individual filters and combined filtering:
    - Website presence (not None, not empty)
    - Minimum review count (default: 10)
    - Open status (exclude permanently closed)
    """

    def filter_has_website(
        self, practices: List[ApifyGoogleMapsResult]
    ) -> List[ApifyGoogleMapsResult]:
        """
        Filter practices that have a valid website (AC-FEAT-001-002).

        Args:
            practices: List of ApifyGoogleMapsResult objects

        Returns:
            Filtered list with only practices that have websites
        """
        filtered = [
            p
            for p in practices
            if p.website is not None and p.website != ""
        ]

        excluded_count = len(practices) - len(filtered)
        if excluded_count > 0:
            logger.info(
                f"Website filter: excluded {excluded_count} practices without websites"
            )

        return filtered

    def filter_min_reviews(
        self,
        practices: List[ApifyGoogleMapsResult],
        min_reviews: int = 10,
    ) -> List[ApifyGoogleMapsResult]:
        """
        Filter practices with minimum review count (AC-FEAT-001-003).

        Args:
            practices: List of ApifyGoogleMapsResult objects
            min_reviews: Minimum review count threshold (default: 10)

        Returns:
            Filtered list with only practices meeting review threshold
        """
        filtered = [
            p
            for p in practices
            if p.google_review_count is not None
            and p.google_review_count >= min_reviews
        ]

        excluded_count = len(practices) - len(filtered)
        if excluded_count > 0:
            logger.info(
                f"Review filter: excluded {excluded_count} practices with <{min_reviews} reviews"
            )

        return filtered

    def filter_is_open(
        self, practices: List[ApifyGoogleMapsResult]
    ) -> List[ApifyGoogleMapsResult]:
        """
        Filter out permanently closed practices (AC-FEAT-001-004).

        Note: Temporarily closed practices are KEPT (they may reopen).

        Args:
            practices: List of ApifyGoogleMapsResult objects

        Returns:
            Filtered list excluding permanently closed practices
        """
        filtered = [p for p in practices if not p.permanently_closed]

        excluded_count = len(practices) - len(filtered)
        if excluded_count > 0:
            logger.info(
                f"Status filter: excluded {excluded_count} permanently closed practices"
            )

        return filtered

    def apply_all_filters(
        self,
        practices: List[ApifyGoogleMapsResult],
        min_reviews: int = 10,
    ) -> List[ApifyGoogleMapsResult]:
        """
        Apply all quality filters in sequence (AC-FEAT-001-002, 003, 004).

        Filter order:
        1. Website presence
        2. Minimum reviews
        3. Open status

        Args:
            practices: List of ApifyGoogleMapsResult objects
            min_reviews: Minimum review count (default: 10)

        Returns:
            Filtered list passing all quality checks
        """
        initial_count = len(practices)

        logger.info(
            f"Applying all filters to {initial_count} practices",
            extra={"initial_count": initial_count, "min_reviews": min_reviews},
        )

        # Apply filters in sequence
        filtered = self.filter_has_website(practices)
        filtered = self.filter_min_reviews(filtered, min_reviews)
        filtered = self.filter_is_open(filtered)

        final_count = len(filtered)
        excluded_count = initial_count - final_count
        pass_rate = (final_count / initial_count * 100) if initial_count > 0 else 0

        logger.info(
            f"Filtering complete: {final_count}/{initial_count} practices passed ({pass_rate:.1f}%)",
            extra={
                "initial_count": initial_count,
                "final_count": final_count,
                "excluded_count": excluded_count,
                "pass_rate": pass_rate,
            },
        )

        return filtered
