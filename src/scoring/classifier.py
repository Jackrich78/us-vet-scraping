"""
Practice Classification for FEAT-003.

Classifies practices by size and assigns priority tiers based on ICP fit scores.
"""

import logging
from typing import Optional
from src.models.scoring_models import PriorityTier, PracticeSizeCategory

logger = logging.getLogger(__name__)


class PracticeClassifier:
    """
    Classifies veterinary practices by size and priority.

    Size Categories:
    - Solo: 1 vet
    - Small: 2 vets
    - Sweet Spot: 3-8 vets (TARGET ICP)
    - Large: 9-19 vets
    - Corporate: 20+ vets

    Priority Tiers:
    - Hot (80-120): Call immediately
    - Warm (50-79): Call soon
    - Cold (20-49): Research or defer
    - Out of Scope (<20): Don't call
    - Pending Enrichment: Awaiting enrichment data
    """

    # Size category thresholds
    SOLO_MAX = 1
    SMALL_MAX = 2
    SWEET_SPOT_MIN = 3
    SWEET_SPOT_MAX = 8
    LARGE_MIN = 9
    LARGE_MAX = 19
    CORPORATE_MIN = 20

    # Priority tier thresholds
    HOT_THRESHOLD = 80
    WARM_THRESHOLD = 50
    COLD_THRESHOLD = 20

    def __init__(self):
        """Initialize the classifier."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def classify_practice_size(self, vet_count: Optional[int]) -> Optional[PracticeSizeCategory]:
        """
        Classify practice by size based on vet count.

        Args:
            vet_count: Number of veterinarians (None if unknown)

        Returns:
            PracticeSizeCategory or None if vet_count is None
        """
        if vet_count is None:
            return None

        if vet_count <= self.SOLO_MAX:
            return PracticeSizeCategory.SOLO
        elif vet_count <= self.SMALL_MAX:
            return PracticeSizeCategory.SMALL
        elif self.SWEET_SPOT_MIN <= vet_count <= self.SWEET_SPOT_MAX:
            return PracticeSizeCategory.SWEET_SPOT
        elif self.LARGE_MIN <= vet_count <= self.LARGE_MAX:
            return PracticeSizeCategory.LARGE
        else:  # 20+
            return PracticeSizeCategory.CORPORATE

    def classify_priority_tier(
        self,
        lead_score: int,
        enrichment_status: Optional[str] = None
    ) -> PriorityTier:
        """
        Classify practice priority tier based on lead score.

        Priority Logic:
        1. If enrichment not completed → Pending Enrichment
        2. Score >= 80 → Hot
        3. Score >= 50 → Warm
        4. Score >= 20 → Cold
        5. Score < 20 → Out of Scope

        Args:
            lead_score: Final ICP fit score (0-120)
            enrichment_status: Enrichment status from FEAT-002 (optional)

        Returns:
            PriorityTier classification
        """
        # Check enrichment status first
        if enrichment_status and enrichment_status not in ["Completed", "Partial"]:
            self.logger.debug(
                f"Practice has enrichment_status='{enrichment_status}' (not Completed/Partial), "
                f"assigning Pending Enrichment tier"
            )
            return PriorityTier.PENDING_ENRICHMENT

        # Classify by score
        if lead_score >= self.HOT_THRESHOLD:
            return PriorityTier.HOT
        elif lead_score >= self.WARM_THRESHOLD:
            return PriorityTier.WARM
        elif lead_score >= self.COLD_THRESHOLD:
            return PriorityTier.COLD
        else:
            return PriorityTier.OUT_OF_SCOPE

    def is_target_icp(self, vet_count: Optional[int], lead_score: int) -> bool:
        """
        Determine if practice matches target ICP criteria.

        Target ICP:
        - Practice size: 3-8 vets (Sweet Spot)
        - Lead score: >= 50 (Warm or Hot)

        Args:
            vet_count: Number of veterinarians
            lead_score: Final ICP fit score

        Returns:
            True if practice is target ICP, False otherwise
        """
        if vet_count is None:
            return False

        size_category = self.classify_practice_size(vet_count)
        priority_tier = self.classify_priority_tier(lead_score)

        is_target = (
            size_category == PracticeSizeCategory.SWEET_SPOT and
            priority_tier in [PriorityTier.HOT, PriorityTier.WARM]
        )

        return is_target

    def get_outreach_recommendation(self, priority_tier: PriorityTier) -> str:
        """
        Get outreach recommendation based on priority tier.

        Args:
            priority_tier: Priority tier classification

        Returns:
            Human-readable recommendation
        """
        recommendations = {
            PriorityTier.HOT: "Call immediately - high ICP fit",
            PriorityTier.WARM: "Schedule call soon - good ICP fit",
            PriorityTier.COLD: "Research further or defer - low ICP fit",
            PriorityTier.OUT_OF_SCOPE: "Do not call - outside target ICP",
            PriorityTier.PENDING_ENRICHMENT: "Awaiting enrichment data - score after enrichment completes"
        }

        return recommendations.get(priority_tier, "Unknown priority tier")

    def get_size_description(self, size_category: Optional[PracticeSizeCategory]) -> str:
        """
        Get human-readable size description.

        Args:
            size_category: Practice size category

        Returns:
            Description string
        """
        if size_category is None:
            return "Unknown size (vet count not available)"

        descriptions = {
            PracticeSizeCategory.SOLO: "Solo practice (1 vet) - may lack decision-making complexity",
            PracticeSizeCategory.SMALL: "Small practice (2 vets) - near target ICP",
            PracticeSizeCategory.SWEET_SPOT: "Sweet spot (3-8 vets) - TARGET ICP",
            PracticeSizeCategory.LARGE: "Large practice (9-19 vets) - near target ICP",
            PracticeSizeCategory.CORPORATE: "Corporate practice (20+ vets) - too large for target ICP"
        }

        return descriptions.get(size_category, "Unknown size category")
