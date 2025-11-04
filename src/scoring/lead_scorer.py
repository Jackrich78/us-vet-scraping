"""
Lead Scoring Calculator for FEAT-003.

Implements the 0-120 point ICP fit scoring system with 5 components:
1. Practice Size & Complexity (0-40 pts)
2. Call Volume Indicators (0-40 pts)
3. Technology Sophistication (0-20 pts)
4. Baseline Quality (0-20 pts)
5. Decision Maker Bonus (0-10 pts)

Total: 0-130 pts before confidence penalty
Final: 0-120 pts after confidence penalty (applied to total score)
"""

import logging
from typing import Tuple, List, Optional
from src.models.scoring_models import (
    ScoringInput,
    ScoringResult,
    ScoreComponent,
    ScoreBreakdown,
    ConfidenceLevel,
    ScoringValidationError
)

logger = logging.getLogger(__name__)


class LeadScorer:
    """
    Calculates ICP fit scores for veterinary practices.

    Scoring Components:
    - Practice Size: 0-40 pts (sweet spot: 3-8 vets, emergency bonus)
    - Call Volume: 0-40 pts (reviews, multiple locations, high-value services)
    - Technology: 0-20 pts (online booking, portal, telemedicine)
    - Baseline: 0-20 pts (rating, reviews, website, multiple locations)
    - Decision Maker: 0-10 pts (name + email bonus)

    Confidence Penalty: Applied to total score
    - High confidence: 1.0x (no penalty)
    - Medium confidence: 0.9x
    - Low confidence: 0.7x
    """

    # Scoring thresholds and constants
    SWEET_SPOT_MIN = 3
    SWEET_SPOT_MAX = 8

    # Practice size scoring
    SWEET_SPOT_BASE_SCORE = 25
    NEAR_SWEET_SPOT_SCORE = 15  # 2 vets or 9 vets
    SOLO_OR_CORPORATE_SCORE = 5  # 1 vet or 10+ vets
    EMERGENCY_BONUS = 15

    # Call volume scoring
    REVIEW_HIGH_THRESHOLD = 100
    REVIEW_HIGH_SCORE = 20
    REVIEW_MEDIUM_THRESHOLD = 50
    REVIEW_MEDIUM_SCORE = 12
    REVIEW_LOW_THRESHOLD = 20
    REVIEW_LOW_SCORE = 5
    MULTIPLE_LOCATIONS_BONUS = 10
    HIGH_VALUE_SERVICES_BONUS = 10

    # Technology scoring
    ONLINE_BOOKING_SCORE = 10
    PORTAL_OR_TELEMEDICINE_SCORE = 5  # Only one applies

    # Baseline scoring (quality/reputation, NOT volume)
    RATING_HIGH_THRESHOLD = 4.5
    RATING_HIGH_SCORE = 10  # Scaled up to reach 20 pts max
    RATING_MEDIUM_THRESHOLD = 4.0
    RATING_MEDIUM_SCORE = 6  # Scaled up
    RATING_LOW_THRESHOLD = 3.5
    RATING_LOW_SCORE = 3  # Scaled up
    WEBSITE_SCORE = 6  # Scaled up
    BASELINE_MULTIPLE_LOCATIONS_SCORE = 4  # Scaled up
    # NOTE: Reviews NOT included in baseline to avoid double-counting with call_volume

    # Decision maker scoring
    DECISION_MAKER_FULL_SCORE = 10  # Name + email
    DECISION_MAKER_PARTIAL_SCORE = 5  # Name only

    # Confidence multipliers
    CONFIDENCE_MULTIPLIERS = {
        ConfidenceLevel.HIGH: 1.0,
        ConfidenceLevel.MEDIUM: 0.9,
        ConfidenceLevel.LOW: 0.7,
    }

    # Max scores per component
    MAX_PRACTICE_SIZE = 40
    MAX_CALL_VOLUME = 40
    MAX_TECHNOLOGY = 20
    MAX_BASELINE = 20
    MAX_DECISION_MAKER = 10

    def __init__(self):
        """Initialize the lead scorer."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def calculate_score(self, scoring_input: ScoringInput) -> ScoringResult:
        """
        Calculate comprehensive ICP fit score for a practice.

        Args:
            scoring_input: Validated scoring input data

        Returns:
            ScoringResult with complete breakdown

        Raises:
            ScoringValidationError: If input data is invalid
        """
        try:
            # Validate input
            self._validate_input(scoring_input)

            # Calculate individual components
            practice_size_comp = self._score_practice_size(scoring_input)
            call_volume_comp = self._score_call_volume(scoring_input)
            technology_comp = self._score_technology(scoring_input)
            baseline_comp = self._score_baseline(scoring_input)
            decision_maker_comp = self._score_decision_maker(scoring_input)

            # Calculate total before confidence penalty
            total_before_confidence = (
                practice_size_comp.score +
                call_volume_comp.score +
                technology_comp.score +
                baseline_comp.score +
                decision_maker_comp.score
            )

            # Determine confidence level and multiplier
            confidence_level = scoring_input.vet_count_confidence or ConfidenceLevel.HIGH
            confidence_multiplier = self.CONFIDENCE_MULTIPLIERS.get(confidence_level, 1.0)

            # Apply confidence penalty to TOTAL score
            total_after_confidence = int(total_before_confidence * confidence_multiplier)

            # Cap at 120 (should not exceed, but safety check)
            total_after_confidence = min(total_after_confidence, 120)

            # Build confidence flags
            confidence_flags = self._build_confidence_flags(scoring_input, confidence_level)

            # Create breakdown
            breakdown = ScoreBreakdown(
                practice_size=practice_size_comp,
                call_volume=call_volume_comp,
                technology=technology_comp,
                baseline=baseline_comp,
                decision_maker=decision_maker_comp,
                total_before_confidence=total_before_confidence,
                confidence_multiplier=confidence_multiplier,
                total_after_confidence=total_after_confidence,
                confidence_level=confidence_level,
                confidence_flags=confidence_flags
            )

            # Determine practice size category (needed for classifier)
            from src.scoring.classifier import PracticeClassifier
            classifier = PracticeClassifier()
            practice_size_category = classifier.classify_practice_size(scoring_input.vet_count_total)
            priority_tier = classifier.classify_priority_tier(
                total_after_confidence,
                scoring_input.enrichment_status
            )

            # Build result
            result = ScoringResult(
                practice_id=scoring_input.practice_id,
                lead_score=total_after_confidence,
                priority_tier=priority_tier,
                practice_size_category=practice_size_category,
                score_breakdown=breakdown,
                confidence_flags=confidence_flags,
                scoring_status="Scored"
            )

            self.logger.info(
                f"Scored practice {scoring_input.practice_id}: "
                f"{total_after_confidence} pts ({priority_tier.value})"
            )

            return result

        except Exception as e:
            self.logger.error(f"Scoring failed for practice {scoring_input.practice_id}: {e}")
            raise ScoringValidationError(f"Failed to calculate score: {e}")

    def _validate_input(self, scoring_input: ScoringInput) -> None:
        """
        Validate scoring input data.

        Args:
            scoring_input: Input to validate

        Raises:
            ScoringValidationError: If validation fails
        """
        if not scoring_input.practice_id:
            raise ScoringValidationError("practice_id is required")

        # Validate vet count if present
        if scoring_input.vet_count_total is not None:
            if scoring_input.vet_count_total < 0 or scoring_input.vet_count_total > 50:
                raise ScoringValidationError(
                    f"Invalid vet_count_total: {scoring_input.vet_count_total} (must be 0-50)"
                )

        # Validate rating if present
        if scoring_input.google_rating is not None:
            if scoring_input.google_rating < 0.0 or scoring_input.google_rating > 5.0:
                raise ScoringValidationError(
                    f"Invalid google_rating: {scoring_input.google_rating} (must be 0.0-5.0)"
                )

    def _score_practice_size(self, scoring_input: ScoringInput) -> ScoreComponent:
        """
        Score practice size and complexity.

        Scoring:
        - 3-8 vets (sweet spot): 25 pts
        - 2 or 9 vets (near sweet spot): 15 pts
        - 1 vet or 10+ vets: 5 pts
        - 24/7 emergency: +15 pts

        Max: 40 pts (25 base + 15 emergency)

        Args:
            scoring_input: Scoring input data

        Returns:
            ScoreComponent with practice size score
        """
        score = 0
        contributing = []
        missing = []

        vet_count = scoring_input.vet_count_total

        if vet_count is None:
            missing.append("Vet count (missing data)")
            detail = "Vet count unknown - cannot score practice size"
        else:
            # Base score by vet count
            if self.SWEET_SPOT_MIN <= vet_count <= self.SWEET_SPOT_MAX:
                score += self.SWEET_SPOT_BASE_SCORE
                contributing.append(f"{vet_count} vets (sweet spot: +{self.SWEET_SPOT_BASE_SCORE} pts)")
            elif vet_count == 2 or vet_count == 9:
                score += self.NEAR_SWEET_SPOT_SCORE
                contributing.append(f"{vet_count} vets (near sweet spot: +{self.NEAR_SWEET_SPOT_SCORE} pts)")
            else:
                score += self.SOLO_OR_CORPORATE_SCORE
                contributing.append(f"{vet_count} vets (solo/corporate: +{self.SOLO_OR_CORPORATE_SCORE} pts)")

            # Emergency bonus
            if scoring_input.emergency_24_7:
                score += self.EMERGENCY_BONUS
                contributing.append(f"24/7 emergency services (+{self.EMERGENCY_BONUS} pts)")
            else:
                missing.append("24/7 emergency services")

            detail = f"{vet_count} vets, emergency={scoring_input.emergency_24_7}"

        # Cap at max
        score = min(score, self.MAX_PRACTICE_SIZE)

        return ScoreComponent(
            score=score,
            max_possible=self.MAX_PRACTICE_SIZE,
            detail=detail,
            contributing_factors=contributing,
            missing_factors=missing
        )

    def _score_call_volume(self, scoring_input: ScoringInput) -> ScoreComponent:
        """
        Score call volume indicators.

        Scoring:
        - 100+ reviews: 20 pts
        - 50-99 reviews: 12 pts
        - 20-49 reviews: 5 pts
        - Multiple locations: +10 pts
        - Boarding OR specialty services: +10 pts

        Max: 40 pts (cap enforced)

        Args:
            scoring_input: Scoring input data

        Returns:
            ScoreComponent with call volume score
        """
        score = 0
        contributing = []
        missing = []

        # Google review count
        review_count = scoring_input.google_review_count or 0
        if review_count >= self.REVIEW_HIGH_THRESHOLD:
            pts = self.REVIEW_HIGH_SCORE
            score += pts
            contributing.append(f"{review_count}+ reviews (+{pts} pts)")
        elif review_count >= self.REVIEW_MEDIUM_THRESHOLD:
            pts = self.REVIEW_MEDIUM_SCORE
            score += pts
            contributing.append(f"{review_count} reviews (+{pts} pts)")
        elif review_count >= self.REVIEW_LOW_THRESHOLD:
            pts = self.REVIEW_LOW_SCORE
            score += pts
            contributing.append(f"{review_count} reviews (+{pts} pts)")
        else:
            missing.append(f"Insufficient reviews ({review_count} < 20)")

        # Multiple locations
        if scoring_input.has_multiple_locations:
            score += self.MULTIPLE_LOCATIONS_BONUS
            contributing.append(f"Multiple locations (+{self.MULTIPLE_LOCATIONS_BONUS} pts)")
        else:
            missing.append("Multiple locations")

        # High-value services (boarding or specialty)
        has_high_value = False
        if scoring_input.specialty_services:
            # Check if boarding is mentioned or if there are specialty services
            has_boarding = any("board" in s.lower() for s in scoring_input.specialty_services)
            has_specialty = len(scoring_input.specialty_services) > 0

            if has_boarding or has_specialty:
                score += self.HIGH_VALUE_SERVICES_BONUS
                contributing.append(
                    f"High-value services ({', '.join(scoring_input.specialty_services[:2])}) "
                    f"(+{self.HIGH_VALUE_SERVICES_BONUS} pts)"
                )
                has_high_value = True

        if not has_high_value:
            missing.append("Boarding or specialty services")

        # Cap at max
        score = min(score, self.MAX_CALL_VOLUME)

        detail = f"{review_count} reviews, {len(scoring_input.specialty_services)} services, multiple_locations={scoring_input.has_multiple_locations}"

        return ScoreComponent(
            score=score,
            max_possible=self.MAX_CALL_VOLUME,
            detail=detail,
            contributing_factors=contributing,
            missing_factors=missing
        )

    def _score_technology(self, scoring_input: ScoringInput) -> ScoreComponent:
        """
        Score technology sophistication.

        Scoring:
        - Online booking: 10 pts
        - Patient portal OR telemedicine: 5 pts (not both)

        Max: 20 pts (with future expansion)

        Args:
            scoring_input: Scoring input data

        Returns:
            ScoreComponent with technology score
        """
        score = 0
        contributing = []
        missing = []

        # Online booking
        if scoring_input.online_booking:
            score += self.ONLINE_BOOKING_SCORE
            contributing.append(f"Online booking (+{self.ONLINE_BOOKING_SCORE} pts)")
        else:
            missing.append("Online booking")

        # Patient portal OR telemedicine (only one counts)
        has_portal_or_tele = False
        if scoring_input.patient_portal:
            score += self.PORTAL_OR_TELEMEDICINE_SCORE
            contributing.append(f"Patient portal (+{self.PORTAL_OR_TELEMEDICINE_SCORE} pts)")
            has_portal_or_tele = True
        elif scoring_input.telemedicine_virtual_care:
            score += self.PORTAL_OR_TELEMEDICINE_SCORE
            contributing.append(f"Telemedicine (+{self.PORTAL_OR_TELEMEDICINE_SCORE} pts)")
            has_portal_or_tele = True

        if not has_portal_or_tele:
            missing.append("Patient portal or telemedicine")

        # Cap at max
        score = min(score, self.MAX_TECHNOLOGY)

        detail = f"booking={scoring_input.online_booking}, portal={scoring_input.patient_portal}, tele={scoring_input.telemedicine_virtual_care}"

        return ScoreComponent(
            score=score,
            max_possible=self.MAX_TECHNOLOGY,
            detail=detail,
            contributing_factors=contributing,
            missing_factors=missing
        )

    def _score_baseline(self, scoring_input: ScoringInput) -> ScoreComponent:
        """
        Score baseline quality from Google Maps data.

        Baseline measures QUALITY/REPUTATION, not volume.
        Reviews are scored in call_volume component to avoid double-counting.

        Scoring:
        - Rating 4.5+: 10 pts
        - Rating 4.0-4.4: 6 pts
        - Rating 3.5-3.9: 3 pts
        - Has website: +6 pts
        - Multiple locations: +4 pts

        Max: 20 pts (10 rating + 6 website + 4 locations)

        Args:
            scoring_input: Scoring input data

        Returns:
            ScoreComponent with baseline score
        """
        score = 0
        contributing = []
        missing = []

        # Rating score (reputation indicator)
        rating = scoring_input.google_rating
        if rating is not None:
            if rating >= self.RATING_HIGH_THRESHOLD:
                pts = self.RATING_HIGH_SCORE
                score += pts
                contributing.append(f"{rating}★ rating (+{pts} pts)")
            elif rating >= self.RATING_MEDIUM_THRESHOLD:
                pts = self.RATING_MEDIUM_SCORE
                score += pts
                contributing.append(f"{rating}★ rating (+{pts} pts)")
            elif rating >= self.RATING_LOW_THRESHOLD:
                pts = self.RATING_LOW_SCORE
                score += pts
                contributing.append(f"{rating}★ rating (+{pts} pts)")
            else:
                missing.append(f"Low rating ({rating}★ < 3.5)")
        else:
            missing.append("Google rating")

        # Website presence (professional indicator)
        if scoring_input.website:
            score += self.WEBSITE_SCORE
            contributing.append(f"Has website (+{self.WEBSITE_SCORE} pts)")
        else:
            missing.append("Website")

        # Multiple locations (growth indicator)
        if scoring_input.has_multiple_locations:
            score += self.BASELINE_MULTIPLE_LOCATIONS_SCORE
            contributing.append(f"Multiple locations (+{self.BASELINE_MULTIPLE_LOCATIONS_SCORE} pts)")
        else:
            missing.append("Multiple locations")

        # Cap at max
        score = min(score, self.MAX_BASELINE)

        detail = f"rating={rating}, website={bool(scoring_input.website)}, multi_loc={scoring_input.has_multiple_locations}"

        return ScoreComponent(
            score=score,
            max_possible=self.MAX_BASELINE,
            detail=detail,
            contributing_factors=contributing,
            missing_factors=missing
        )

    def _score_decision_maker(self, scoring_input: ScoringInput) -> ScoreComponent:
        """
        Score decision maker identification.

        Scoring:
        - Name + email: 10 pts
        - Name only: 5 pts
        - No decision maker: 0 pts

        Max: 10 pts

        Args:
            scoring_input: Scoring input data

        Returns:
            ScoreComponent with decision maker score
        """
        score = 0
        contributing = []
        missing = []

        has_name = bool(scoring_input.decision_maker_name)
        has_email = bool(scoring_input.decision_maker_email)

        if has_name and has_email:
            score = self.DECISION_MAKER_FULL_SCORE
            contributing.append(
                f"Decision maker identified: {scoring_input.decision_maker_name} "
                f"<{scoring_input.decision_maker_email}> (+{self.DECISION_MAKER_FULL_SCORE} pts)"
            )
            detail = f"Name + email: {scoring_input.decision_maker_name}"
        elif has_name:
            score = self.DECISION_MAKER_PARTIAL_SCORE
            contributing.append(
                f"Decision maker name only: {scoring_input.decision_maker_name} "
                f"(+{self.DECISION_MAKER_PARTIAL_SCORE} pts)"
            )
            missing.append("Decision maker email")
            detail = f"Name only: {scoring_input.decision_maker_name}"
        else:
            missing.append("Decision maker name and email")
            detail = "No decision maker identified"

        return ScoreComponent(
            score=score,
            max_possible=self.MAX_DECISION_MAKER,
            detail=detail,
            contributing_factors=contributing,
            missing_factors=missing
        )

    def _build_confidence_flags(
        self,
        scoring_input: ScoringInput,
        confidence_level: ConfidenceLevel
    ) -> List[str]:
        """
        Build list of confidence warning flags.

        Args:
            scoring_input: Scoring input data
            confidence_level: Overall confidence level

        Returns:
            List of warning strings
        """
        flags = []

        if confidence_level == ConfidenceLevel.LOW:
            flags.append(f"Low confidence enrichment data (penalty: {self.CONFIDENCE_MULTIPLIERS[ConfidenceLevel.LOW]}x)")
        elif confidence_level == ConfidenceLevel.MEDIUM:
            flags.append(f"Medium confidence enrichment data (penalty: {self.CONFIDENCE_MULTIPLIERS[ConfidenceLevel.MEDIUM]}x)")

        if scoring_input.vet_count_total is None:
            flags.append("Missing vet count - practice size not scored")

        if not scoring_input.decision_maker_name:
            flags.append("No decision maker identified")

        if not scoring_input.google_rating:
            flags.append("Missing Google rating")

        return flags
