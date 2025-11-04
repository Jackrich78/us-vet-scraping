"""
Unit tests for FEAT-003 Practice Classifier.

Tests practice size categorization and priority tier assignment.
"""

import pytest
from src.scoring.classifier import PracticeClassifier
from src.models.scoring_models import PriorityTier, PracticeSizeCategory


class TestPracticeSizeClassification:
    """Test practice size categorization."""

    def test_solo_1_vet(self):
        """1 vet classified as Solo."""
        classifier = PracticeClassifier()
        assert classifier.classify_practice_size(1) == PracticeSizeCategory.SOLO

    def test_small_2_vets(self):
        """2 vets classified as Small."""
        classifier = PracticeClassifier()
        assert classifier.classify_practice_size(2) == PracticeSizeCategory.SMALL

    def test_sweet_spot_3_vets(self):
        """3 vets classified as Sweet Spot (minimum)."""
        classifier = PracticeClassifier()
        assert classifier.classify_practice_size(3) == PracticeSizeCategory.SWEET_SPOT

    def test_sweet_spot_5_vets(self):
        """5 vets classified as Sweet Spot (middle)."""
        classifier = PracticeClassifier()
        assert classifier.classify_practice_size(5) == PracticeSizeCategory.SWEET_SPOT

    def test_sweet_spot_8_vets(self):
        """8 vets classified as Sweet Spot (maximum)."""
        classifier = PracticeClassifier()
        assert classifier.classify_practice_size(8) == PracticeSizeCategory.SWEET_SPOT

    def test_large_9_vets(self):
        """9 vets classified as Large (minimum)."""
        classifier = PracticeClassifier()
        assert classifier.classify_practice_size(9) == PracticeSizeCategory.LARGE

    def test_large_15_vets(self):
        """15 vets classified as Large (middle)."""
        classifier = PracticeClassifier()
        assert classifier.classify_practice_size(15) == PracticeSizeCategory.LARGE

    def test_large_19_vets(self):
        """19 vets classified as Large (maximum)."""
        classifier = PracticeClassifier()
        assert classifier.classify_practice_size(19) == PracticeSizeCategory.LARGE

    def test_corporate_20_vets(self):
        """20 vets classified as Corporate (minimum)."""
        classifier = PracticeClassifier()
        assert classifier.classify_practice_size(20) == PracticeSizeCategory.CORPORATE

    def test_corporate_50_vets(self):
        """50 vets classified as Corporate."""
        classifier = PracticeClassifier()
        assert classifier.classify_practice_size(50) == PracticeSizeCategory.CORPORATE

    def test_none_vet_count(self):
        """None vet count returns None."""
        classifier = PracticeClassifier()
        assert classifier.classify_practice_size(None) is None


class TestPriorityTierClassification:
    """Test priority tier assignment based on scores."""

    def test_hot_tier_80_pts(self):
        """Score 80 classified as Hot (minimum)."""
        classifier = PracticeClassifier()
        assert classifier.classify_priority_tier(80) == PriorityTier.HOT

    def test_hot_tier_100_pts(self):
        """Score 100 classified as Hot."""
        classifier = PracticeClassifier()
        assert classifier.classify_priority_tier(100) == PriorityTier.HOT

    def test_hot_tier_120_pts(self):
        """Score 120 classified as Hot (maximum)."""
        classifier = PracticeClassifier()
        assert classifier.classify_priority_tier(120) == PriorityTier.HOT

    def test_warm_tier_50_pts(self):
        """Score 50 classified as Warm (minimum)."""
        classifier = PracticeClassifier()
        assert classifier.classify_priority_tier(50) == PriorityTier.WARM

    def test_warm_tier_65_pts(self):
        """Score 65 classified as Warm."""
        classifier = PracticeClassifier()
        assert classifier.classify_priority_tier(65) == PriorityTier.WARM

    def test_warm_tier_79_pts(self):
        """Score 79 classified as Warm (maximum)."""
        classifier = PracticeClassifier()
        assert classifier.classify_priority_tier(79) == PriorityTier.WARM

    def test_cold_tier_20_pts(self):
        """Score 20 classified as Cold (minimum)."""
        classifier = PracticeClassifier()
        assert classifier.classify_priority_tier(20) == PriorityTier.COLD

    def test_cold_tier_35_pts(self):
        """Score 35 classified as Cold."""
        classifier = PracticeClassifier()
        assert classifier.classify_priority_tier(35) == PriorityTier.COLD

    def test_cold_tier_49_pts(self):
        """Score 49 classified as Cold (maximum)."""
        classifier = PracticeClassifier()
        assert classifier.classify_priority_tier(49) == PriorityTier.COLD

    def test_out_of_scope_0_pts(self):
        """Score 0 classified as Out of Scope."""
        classifier = PracticeClassifier()
        assert classifier.classify_priority_tier(0) == PriorityTier.OUT_OF_SCOPE

    def test_out_of_scope_19_pts(self):
        """Score 19 classified as Out of Scope (maximum)."""
        classifier = PracticeClassifier()
        assert classifier.classify_priority_tier(19) == PriorityTier.OUT_OF_SCOPE

    def test_pending_enrichment_status(self):
        """Enrichment status not Completed → Pending Enrichment."""
        classifier = PracticeClassifier()

        # High score but not enriched
        assert classifier.classify_priority_tier(
            100,
            enrichment_status="New"
        ) == PriorityTier.PENDING_ENRICHMENT

        assert classifier.classify_priority_tier(
            100,
            enrichment_status="Failed"
        ) == PriorityTier.PENDING_ENRICHMENT

    def test_completed_enrichment_uses_score(self):
        """Enrichment status Completed → uses score for tier."""
        classifier = PracticeClassifier()

        assert classifier.classify_priority_tier(
            90,
            enrichment_status="Completed"
        ) == PriorityTier.HOT

    def test_partial_enrichment_uses_score(self):
        """Enrichment status Partial → uses score for tier."""
        classifier = PracticeClassifier()

        assert classifier.classify_priority_tier(
            60,
            enrichment_status="Partial"
        ) == PriorityTier.WARM


class TestTargetICPIdentification:
    """Test target ICP identification logic."""

    def test_target_icp_sweet_spot_hot(self):
        """Sweet spot (5 vets) + Hot (90 pts) = target ICP."""
        classifier = PracticeClassifier()
        assert classifier.is_target_icp(5, 90) is True

    def test_target_icp_sweet_spot_warm(self):
        """Sweet spot (5 vets) + Warm (60 pts) = target ICP."""
        classifier = PracticeClassifier()
        assert classifier.is_target_icp(5, 60) is True

    def test_not_target_icp_sweet_spot_cold(self):
        """Sweet spot (5 vets) + Cold (30 pts) = NOT target ICP."""
        classifier = PracticeClassifier()
        assert classifier.is_target_icp(5, 30) is False

    def test_not_target_icp_solo_hot(self):
        """Solo (1 vet) + Hot (90 pts) = NOT target ICP."""
        classifier = PracticeClassifier()
        assert classifier.is_target_icp(1, 90) is False

    def test_not_target_icp_corporate_hot(self):
        """Corporate (20 vets) + Hot (90 pts) = NOT target ICP."""
        classifier = PracticeClassifier()
        assert classifier.is_target_icp(20, 90) is False

    def test_not_target_icp_none_vet_count(self):
        """None vet count = NOT target ICP."""
        classifier = PracticeClassifier()
        assert classifier.is_target_icp(None, 100) is False

    def test_target_icp_boundary_3_vets_50_pts(self):
        """Boundary: 3 vets + 50 pts = target ICP."""
        classifier = PracticeClassifier()
        assert classifier.is_target_icp(3, 50) is True

    def test_target_icp_boundary_8_vets_50_pts(self):
        """Boundary: 8 vets + 50 pts = target ICP."""
        classifier = PracticeClassifier()
        assert classifier.is_target_icp(8, 50) is True


class TestOutreachRecommendations:
    """Test outreach recommendation text generation."""

    def test_hot_recommendation(self):
        """Hot tier recommends immediate call."""
        classifier = PracticeClassifier()
        rec = classifier.get_outreach_recommendation(PriorityTier.HOT)
        assert "immediately" in rec.lower()
        assert "high icp fit" in rec.lower()

    def test_warm_recommendation(self):
        """Warm tier recommends call soon."""
        classifier = PracticeClassifier()
        rec = classifier.get_outreach_recommendation(PriorityTier.WARM)
        assert "soon" in rec.lower()
        assert "good icp fit" in rec.lower()

    def test_cold_recommendation(self):
        """Cold tier recommends research or defer."""
        classifier = PracticeClassifier()
        rec = classifier.get_outreach_recommendation(PriorityTier.COLD)
        assert "research" in rec.lower() or "defer" in rec.lower()

    def test_out_of_scope_recommendation(self):
        """Out of scope recommends no call."""
        classifier = PracticeClassifier()
        rec = classifier.get_outreach_recommendation(PriorityTier.OUT_OF_SCOPE)
        assert "do not call" in rec.lower()

    def test_pending_enrichment_recommendation(self):
        """Pending enrichment recommends waiting."""
        classifier = PracticeClassifier()
        rec = classifier.get_outreach_recommendation(PriorityTier.PENDING_ENRICHMENT)
        assert "awaiting" in rec.lower() or "enrichment" in rec.lower()


class TestSizeDescriptions:
    """Test size description text generation."""

    def test_solo_description(self):
        """Solo description mentions 1 vet."""
        classifier = PracticeClassifier()
        desc = classifier.get_size_description(PracticeSizeCategory.SOLO)
        assert "1 vet" in desc.lower()
        assert "solo" in desc.lower()

    def test_small_description(self):
        """Small description mentions 2 vets."""
        classifier = PracticeClassifier()
        desc = classifier.get_size_description(PracticeSizeCategory.SMALL)
        assert "2 vets" in desc.lower()

    def test_sweet_spot_description(self):
        """Sweet spot description mentions target ICP."""
        classifier = PracticeClassifier()
        desc = classifier.get_size_description(PracticeSizeCategory.SWEET_SPOT)
        assert "3-8 vets" in desc.lower()
        assert "target icp" in desc.lower()

    def test_large_description(self):
        """Large description mentions 9-19 vets."""
        classifier = PracticeClassifier()
        desc = classifier.get_size_description(PracticeSizeCategory.LARGE)
        assert "9-19 vets" in desc.lower()

    def test_corporate_description(self):
        """Corporate description mentions 20+ vets."""
        classifier = PracticeClassifier()
        desc = classifier.get_size_description(PracticeSizeCategory.CORPORATE)
        assert "20+ vets" in desc.lower()

    def test_none_size_description(self):
        """None size returns unknown message."""
        classifier = PracticeClassifier()
        desc = classifier.get_size_description(None)
        assert "unknown" in desc.lower()
