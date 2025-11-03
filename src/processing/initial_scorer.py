"""
Initial lead scoring for veterinary practices (FEAT-001).

Calculates baseline ICP fit score (0-25 points) based on:
- Review count (0-15 points): More reviews = higher credibility
- Star rating (0-10 points): Higher rating = better quality

Scoring algorithm (AC-FEAT-001-005):
- Review count score:
  * 0-49 reviews: 5 points
  * 50-149 reviews: 10 points
  * 150+ reviews: 15 points

- Star rating score:
  * <3.5 stars: 0 points
  * 3.5-3.9 stars: 3 points
  * 4.0-4.4 stars: 6 points
  * 4.5+ stars: 10 points

Total: 0-25 points (higher = better ICP fit)
"""

import logging
from typing import List
from src.models.apify_models import ApifyGoogleMapsResult
from src.models.apify_models import VeterinaryPractice

logger = logging.getLogger(__name__)


class InitialScorer:
    """
    Lead scoring service for veterinary practices.

    Calculates initial ICP fit score (0-25 points) based on
    review count and star rating using tiered scoring.
    """

    def calculate_baseline_score(self, practice: ApifyGoogleMapsResult) -> int:
        """
        Calculate initial lead score (0-25 points) for a practice (AC-FEAT-001-005).

        Args:
            practice: ApifyGoogleMapsResult with review data

        Returns:
            Score from 0-25 (review score + rating score)
        """
        review_score = self._calculate_review_score(practice.google_review_count)
        rating_score = self._calculate_rating_score(practice.google_rating)

        total_score = review_score + rating_score

        logger.debug(
            f"Scored practice {practice.place_id}: {total_score} pts "
            f"(reviews={review_score}, rating={rating_score})"
        )

        return total_score

    def _calculate_review_score(self, review_count: int | None) -> int:
        """
        Calculate review count score (0-15 points).

        Tiers:
        - 0-49 reviews: 5 points
        - 50-149 reviews: 10 points
        - 150+ reviews: 15 points

        Args:
            review_count: Number of Google reviews

        Returns:
            Score from 0-15 points
        """
        if review_count is None or review_count < 0:
            return 0

        if review_count < 50:
            return 5
        elif review_count < 150:
            return 10
        else:  # 150+
            return 15

    def _calculate_rating_score(self, rating: float | None) -> int:
        """
        Calculate star rating score (0-10 points).

        Tiers:
        - <3.5 stars: 0 points
        - 3.5-3.9 stars: 3 points
        - 4.0-4.4 stars: 6 points
        - 4.5+ stars: 10 points

        Args:
            rating: Google star rating (0.0-5.0)

        Returns:
            Score from 0-10 points
        """
        if rating is None or rating < 0:
            return 0

        if rating < 3.5:
            return 0
        elif rating < 4.0:
            return 3
        elif rating < 4.5:
            return 6
        else:  # 4.5+
            return 10

    def score_batch(
        self, practices: List[ApifyGoogleMapsResult]
    ) -> List[VeterinaryPractice]:
        """
        Score a batch of practices and convert to VeterinaryPractice models (AC-FEAT-001-005).

        Args:
            practices: List of ApifyGoogleMapsResult objects

        Returns:
            List of VeterinaryPractice objects with initial_score added
        """
        scored_practices = []

        for practice in practices:
            score = self.calculate_baseline_score(practice)

            # Convert to VeterinaryPractice with score
            scored_practice = VeterinaryPractice(
                place_id=practice.place_id,
                practice_name=practice.practice_name,
                address=practice.address,
                phone=practice.phone,
                website=practice.website,
                google_rating=practice.google_rating,
                google_review_count=practice.google_review_count,
                business_categories=practice.business_categories,
                postal_code=practice.postal_code,
                permanently_closed=practice.permanently_closed,
                initial_score=score,
                priority_tier=self._determine_priority_tier(score),
            )

            scored_practices.append(scored_practice)

        logger.info(
            f"Batch scoring complete: {len(scored_practices)} practices scored",
            extra={
                "count": len(scored_practices),
                "avg_score": sum(p.initial_score for p in scored_practices)
                / len(scored_practices)
                if scored_practices
                else 0,
            },
        )

        return scored_practices

    def _determine_priority_tier(self, score: int) -> str:
        """
        Determine priority tier based on score.

        Tiers:
        - Hot: 20-25 points (top tier)
        - Warm: 15-19 points (mid tier)
        - Cold: 0-14 points (low tier)

        Args:
            score: Initial score (0-25)

        Returns:
            Priority tier: "Hot", "Warm", or "Cold"
        """
        if score >= 20:
            return "Hot"
        elif score >= 15:
            return "Warm"
        else:
            return "Cold"
