"""
Unit tests for FEAT-003 Lead Scorer.

Tests all 5 scoring components and confidence penalty logic.
"""

import pytest
from src.scoring.lead_scorer import LeadScorer
from src.models.scoring_models import (
    ScoringInput,
    ConfidenceLevel,
    PriorityTier,
    PracticeSizeCategory,
    ScoringValidationError
)


class TestLeadScorerPracticeSize:
    """Test practice size and complexity scoring (0-40 pts)."""

    def test_sweet_spot_3_vets(self):
        """3 vets (sweet spot minimum) scores 25 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-001",
            vet_count_total=3
        )

        component = scorer._score_practice_size(scoring_input)

        assert component.score == 25
        assert "3 vets (sweet spot: +25 pts)" in component.contributing_factors[0]

    def test_sweet_spot_8_vets(self):
        """8 vets (sweet spot maximum) scores 25 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-002",
            vet_count_total=8
        )

        component = scorer._score_practice_size(scoring_input)

        assert component.score == 25

    def test_near_sweet_spot_2_vets(self):
        """2 vets (near sweet spot) scores 15 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-003",
            vet_count_total=2
        )

        component = scorer._score_practice_size(scoring_input)

        assert component.score == 15
        assert "2 vets (near sweet spot: +15 pts)" in component.contributing_factors[0]

    def test_near_sweet_spot_9_vets(self):
        """9 vets (near sweet spot) scores 15 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-004",
            vet_count_total=9
        )

        component = scorer._score_practice_size(scoring_input)

        assert component.score == 15

    def test_solo_practice_1_vet(self):
        """1 vet (solo) scores 5 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-005",
            vet_count_total=1
        )

        component = scorer._score_practice_size(scoring_input)

        assert component.score == 5
        assert "1 vets (solo/corporate: +5 pts)" in component.contributing_factors[0]

    def test_corporate_10_plus_vets(self):
        """10+ vets (corporate) scores 5 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-006",
            vet_count_total=15
        )

        component = scorer._score_practice_size(scoring_input)

        assert component.score == 5

    def test_emergency_bonus(self):
        """24/7 emergency adds 15 pts bonus."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-007",
            vet_count_total=5,
            emergency_24_7=True
        )

        component = scorer._score_practice_size(scoring_input)

        assert component.score == 40  # 25 base + 15 emergency
        assert "24/7 emergency services (+15 pts)" in component.contributing_factors[1]

    def test_missing_vet_count(self):
        """Missing vet count scores 0 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-008",
            vet_count_total=None
        )

        component = scorer._score_practice_size(scoring_input)

        assert component.score == 0
        assert "Vet count (missing data)" in component.missing_factors


class TestLeadScorerCallVolume:
    """Test call volume indicators scoring (0-40 pts)."""

    def test_high_review_count_100_plus(self):
        """100+ reviews scores 20 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-009",
            google_review_count=150
        )

        component = scorer._score_call_volume(scoring_input)

        assert component.score == 20
        assert "150+ reviews (+20 pts)" in component.contributing_factors[0]

    def test_medium_review_count_50_99(self):
        """50-99 reviews scores 12 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-010",
            google_review_count=75
        )

        component = scorer._score_call_volume(scoring_input)

        assert component.score == 12

    def test_low_review_count_20_49(self):
        """20-49 reviews scores 5 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-011",
            google_review_count=30
        )

        component = scorer._score_call_volume(scoring_input)

        assert component.score == 5

    def test_multiple_locations_bonus(self):
        """Multiple locations adds 10 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-012",
            google_review_count=100,
            has_multiple_locations=True
        )

        component = scorer._score_call_volume(scoring_input)

        assert component.score == 30  # 20 reviews + 10 locations
        assert "Multiple locations (+10 pts)" in component.contributing_factors[1]

    def test_specialty_services_bonus(self):
        """Specialty services add 10 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-013",
            google_review_count=100,
            specialty_services=["Surgery", "Dentistry"]
        )

        component = scorer._score_call_volume(scoring_input)

        assert component.score == 30  # 20 reviews + 10 services
        assert "High-value services" in component.contributing_factors[1]

    def test_boarding_in_services(self):
        """Boarding service adds 10 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-014",
            google_review_count=50,
            specialty_services=["Boarding"]
        )

        component = scorer._score_call_volume(scoring_input)

        assert component.score == 22  # 12 reviews + 10 boarding

    def test_cap_at_40_pts(self):
        """Call volume capped at 40 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-015",
            google_review_count=200,
            has_multiple_locations=True,
            specialty_services=["Surgery", "Dentistry", "Boarding"]
        )

        component = scorer._score_call_volume(scoring_input)

        assert component.score == 40  # Cap enforced (would be 20+10+10=40)


class TestLeadScorerTechnology:
    """Test technology sophistication scoring (0-20 pts)."""

    def test_online_booking(self):
        """Online booking scores 10 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-016",
            online_booking=True
        )

        component = scorer._score_technology(scoring_input)

        assert component.score == 10
        assert "Online booking (+10 pts)" in component.contributing_factors[0]

    def test_patient_portal(self):
        """Patient portal scores 5 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-017",
            patient_portal=True
        )

        component = scorer._score_technology(scoring_input)

        assert component.score == 5
        assert "Patient portal (+5 pts)" in component.contributing_factors[0]

    def test_telemedicine(self):
        """Telemedicine scores 5 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-018",
            telemedicine_virtual_care=True
        )

        component = scorer._score_technology(scoring_input)

        assert component.score == 5

    def test_portal_and_telemedicine_only_one_counts(self):
        """Portal + telemedicine = only 5 pts (not 10)."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-019",
            patient_portal=True,
            telemedicine_virtual_care=True
        )

        component = scorer._score_technology(scoring_input)

        # Only patient portal counts (first one checked)
        assert component.score == 5

    def test_all_technology_features(self):
        """All tech features score 15 pts max."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-020",
            online_booking=True,
            patient_portal=True,
            telemedicine_virtual_care=True
        )

        component = scorer._score_technology(scoring_input)

        assert component.score == 15  # 10 booking + 5 portal (tele doesn't stack)


class TestLeadScorerBaseline:
    """Test baseline quality scoring (0-20 pts)."""

    def test_high_rating_4_5_plus(self):
        """Rating 4.5+ scores 10 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-021",
            google_rating=4.8
        )

        component = scorer._score_baseline(scoring_input)

        assert component.score == 10
        assert "4.8★ rating (+10 pts)" in component.contributing_factors[0]

    def test_medium_rating_4_0_to_4_4(self):
        """Rating 4.0-4.4 scores 6 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-022",
            google_rating=4.2
        )

        component = scorer._score_baseline(scoring_input)

        assert component.score == 6

    def test_low_rating_3_5_to_3_9(self):
        """Rating 3.5-3.9 scores 3 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-023",
            google_rating=3.7
        )

        component = scorer._score_baseline(scoring_input)

        assert component.score == 3

    def test_baseline_no_reviews(self):
        """Baseline does NOT include reviews (to avoid double-counting)."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-024",
            google_rating=4.5,
            google_review_count=100
        )

        component = scorer._score_baseline(scoring_input)

        # Only rating, no reviews
        assert component.score == 10  # 10 rating only

    def test_website_presence(self):
        """Website presence adds 6 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-025",
            google_rating=4.5,
            website="https://example.com"
        )

        component = scorer._score_baseline(scoring_input)

        assert component.score == 16  # 10 rating + 6 website

    def test_baseline_multiple_locations(self):
        """Multiple locations adds 4 pts in baseline."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-026",
            google_rating=4.5,
            has_multiple_locations=True
        )

        component = scorer._score_baseline(scoring_input)

        assert component.score == 14  # 10 rating + 4 locations

    def test_baseline_max_20_pts(self):
        """Baseline maxes at 20 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-027",
            google_rating=4.8,
            google_review_count=150,  # Reviews NOT counted in baseline
            website="https://example.com",
            has_multiple_locations=True
        )

        component = scorer._score_baseline(scoring_input)

        assert component.score == 20  # 10 rating + 6 website + 4 locations


class TestLeadScorerDecisionMaker:
    """Test decision maker bonus scoring (0-10 pts)."""

    def test_name_and_email(self):
        """Name + email scores 10 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-028",
            decision_maker_name="Dr. Smith",
            decision_maker_email="smith@example.com"
        )

        component = scorer._score_decision_maker(scoring_input)

        assert component.score == 10
        assert "Dr. Smith" in component.contributing_factors[0]
        assert "smith@example.com" in component.contributing_factors[0]

    def test_name_only(self):
        """Name only scores 5 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-029",
            decision_maker_name="Dr. Johnson"
        )

        component = scorer._score_decision_maker(scoring_input)

        assert component.score == 5
        assert "name only" in component.contributing_factors[0]

    def test_no_decision_maker(self):
        """No decision maker scores 0 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-030"
        )

        component = scorer._score_decision_maker(scoring_input)

        assert component.score == 0
        assert "No decision maker identified" in component.detail


class TestLeadScorerConfidencePenalty:
    """Test confidence penalty application to total score."""

    def test_high_confidence_no_penalty(self):
        """High confidence = 1.0x multiplier (no penalty)."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-031",
            vet_count_total=5,
            vet_count_confidence=ConfidenceLevel.HIGH,
            google_rating=4.5,
            google_review_count=100,
            website="https://example.com"
        )

        result = scorer.calculate_score(scoring_input)

        # Total before: 25 (practice_size) + 20 (call_volume:reviews) + 16 (baseline: 10 rating + 6 website) = 61
        assert result.score_breakdown.confidence_multiplier == 1.0
        assert result.score_breakdown.total_after_confidence == 61

    def test_medium_confidence_penalty(self):
        """Medium confidence = 0.9x multiplier."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-032",
            vet_count_total=5,
            vet_count_confidence=ConfidenceLevel.MEDIUM,
            google_rating=4.5,
            google_review_count=100,
            website="https://example.com"
        )

        result = scorer.calculate_score(scoring_input)

        # Total before: 61
        # After: 61 * 0.9 = 54.9 → 54 (int)
        assert result.score_breakdown.confidence_multiplier == 0.9
        assert result.score_breakdown.total_before_confidence == 61
        assert result.score_breakdown.total_after_confidence == 54

    def test_low_confidence_penalty(self):
        """Low confidence = 0.7x multiplier."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-033",
            vet_count_total=5,
            vet_count_confidence=ConfidenceLevel.LOW,
            google_rating=4.5,
            google_review_count=100,
            website="https://example.com"
        )

        result = scorer.calculate_score(scoring_input)

        # Total before: 61
        # After: 61 * 0.7 = 42.7 → 42 (int)
        assert result.score_breakdown.confidence_multiplier == 0.7
        assert result.score_breakdown.total_after_confidence == 42


class TestLeadScorerCompleteScenarios:
    """Test complete scoring scenarios from PRD."""

    def test_perfect_score_scenario(self):
        """Perfect practice scores near 120 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-034",
            # Practice size: 40 pts (25 sweet spot + 15 emergency)
            vet_count_total=5,
            vet_count_confidence=ConfidenceLevel.HIGH,
            emergency_24_7=True,
            # Call volume: 40 pts (20 reviews + 10 locations + 10 services)
            google_review_count=150,
            has_multiple_locations=True,
            specialty_services=["Surgery", "Dentistry"],
            # Technology: 15 pts (10 booking + 5 portal)
            online_booking=True,
            patient_portal=True,
            # Baseline: 20 pts (6 rating + 8 reviews + 4 website + 2 locations)
            google_rating=4.8,
            website="https://example.com",
            # Decision maker: 10 pts
            decision_maker_name="Dr. Smith",
            decision_maker_email="smith@example.com"
        )

        result = scorer.calculate_score(scoring_input)

        # Total: 40 + 40 + 15 + 20 + 10 = 125 before confidence
        # But baseline should cap at 20, call_volume at 40, so actual total = 125
        # Wait, need to recalculate:
        # Practice: 40, Call: 40, Tech: 15, Baseline: 20, DM: 10 = 125
        # Confidence: 1.0x = 125, capped at 120
        assert result.lead_score == 120  # Capped
        assert result.priority_tier == PriorityTier.HOT

    def test_baseline_only_scenario(self):
        """Unenriched practice (baseline only) scores < 40 pts."""
        scorer = LeadScorer()
        scoring_input = ScoringInput(
            practice_id="test-035",
            # Only Google Maps data
            google_rating=4.5,
            google_review_count=75,
            website="https://example.com",
            has_multiple_locations=False,
            # No enrichment data
            vet_count_total=None
        )

        result = scorer.calculate_score(scoring_input)

        # Call volume: 12 (reviews 50-99)
        # Baseline: 10 (rating) + 6 (website) = 16
        # Total: 12 + 16 = 28
        assert result.lead_score == 28
        assert result.priority_tier == PriorityTier.COLD


    def test_validation_error_invalid_vet_count(self):
        """Invalid vet count raises Pydantic validation error."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="vet_count_total"):
            scoring_input = ScoringInput(
                practice_id="test-036",
                vet_count_total=100  # Invalid: > 50
            )

    def test_validation_error_invalid_rating(self):
        """Invalid rating raises Pydantic validation error."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="google_rating"):
            scoring_input = ScoringInput(
                practice_id="test-037",
                google_rating=6.0  # Invalid: > 5.0
            )
