"""
Unit tests for InitialScorer (FEAT-001).

Tests baseline lead scoring algorithm (0-25 points):
- Review count score: 0-15 points (tiered)
- Star rating score: 0-10 points (tiered)
Total: 0-25 points initial ICP fit score
"""

import pytest
from src.processing.initial_scorer import InitialScorer
from src.models.apify_models import ApifyGoogleMapsResult


class TestInitialScorer:
    """Test InitialScorer class functionality."""

    def test_calculate_score_max_score(self):
        """AC-FEAT-001-005: Maximum score is 25 points (150+ reviews, 4.5+ rating)."""
        # Given: Practice with optimal attributes
        practice = ApifyGoogleMapsResult(
            place_id="ChIJmax",
            practice_name="Top Rated Vet",
            address="123 St",
            website="https://topvet.com",
            google_review_count=150,  # 15 pts
            google_rating=5.0,  # 10 pts
            permanently_closed=False,
        )

        scorer = InitialScorer()

        # When: Calculating score
        score = scorer.calculate_baseline_score(practice)

        # Then: Returns maximum score of 25
        assert score == 25

    def test_calculate_score_min_score(self):
        """AC-FEAT-001-005: Minimum passing score (10 reviews, 3.5 rating) = 8 points."""
        # Given: Practice with minimum passing attributes
        practice = ApifyGoogleMapsResult(
            place_id="ChIJmin",
            practice_name="Basic Vet",
            address="123 St",
            website="https://basicvet.com",
            google_review_count=10,  # 5 pts (0-49 tier)
            google_rating=3.5,  # 3 pts (3.5-3.9 tier)
            permanently_closed=False,
        )

        scorer = InitialScorer()

        # When: Calculating score
        score = scorer.calculate_baseline_score(practice)

        # Then: Returns low score
        assert score == 8  # 5 + 3 = 8

    def test_calculate_score_review_weight(self):
        """AC-FEAT-001-005: Review count contributes 0-15 points in tiers."""
        # Given: Practices with different review counts (same rating)
        practices = [
            ApifyGoogleMapsResult(
                place_id="1",
                practice_name="10 Reviews",
                address="1 St",
                website="https://test.com",
                google_review_count=10,  # 5 pts (0-49 tier)
                google_rating=4.0,
                permanently_closed=False,
            ),
            ApifyGoogleMapsResult(
                place_id="2",
                practice_name="50 Reviews",
                address="2 St",
                website="https://test.com",
                google_review_count=50,  # 10 pts (50-149 tier)
                google_rating=4.0,
                permanently_closed=False,
            ),
            ApifyGoogleMapsResult(
                place_id="3",
                practice_name="150 Reviews",
                address="3 St",
                website="https://test.com",
                google_review_count=150,  # 15 pts (150+ tier)
                google_rating=4.0,
                permanently_closed=False,
            ),
        ]

        scorer = InitialScorer()

        # When: Calculating scores
        scores = [scorer.calculate_baseline_score(p) for p in practices]

        # Then: Scores increase with review count in tiers
        assert scores[0] == 11  # 5 (reviews) + 6 (rating) = 11
        assert scores[1] == 16  # 10 (reviews) + 6 (rating) = 16
        assert scores[2] == 21  # 15 (reviews) + 6 (rating) = 21
        assert scores[0] < scores[1] < scores[2]

    def test_calculate_score_rating_weight(self):
        """AC-FEAT-001-005: Star rating contributes 0-10 points in tiers."""
        # Given: Practices with different ratings (same review count)
        practices = [
            ApifyGoogleMapsResult(
                place_id="1",
                practice_name="3.5 Rating",
                address="1 St",
                website="https://test.com",
                google_review_count=50,
                google_rating=3.5,  # 3 pts (3.5-3.9 tier)
                permanently_closed=False,
            ),
            ApifyGoogleMapsResult(
                place_id="2",
                practice_name="4.0 Rating",
                address="2 St",
                website="https://test.com",
                google_review_count=50,
                google_rating=4.0,  # 6 pts (4.0-4.4 tier)
                permanently_closed=False,
            ),
            ApifyGoogleMapsResult(
                place_id="3",
                practice_name="4.5 Rating",
                address="3 St",
                website="https://test.com",
                google_review_count=50,
                google_rating=4.5,  # 10 pts (4.5+ tier)
                permanently_closed=False,
            ),
        ]

        scorer = InitialScorer()

        # When: Calculating scores
        scores = [scorer.calculate_baseline_score(p) for p in practices]

        # Then: Scores increase with rating in tiers
        assert scores[0] == 13  # 10 (reviews) + 3 (rating) = 13
        assert scores[1] == 16  # 10 (reviews) + 6 (rating) = 16
        assert scores[2] == 20  # 10 (reviews) + 10 (rating) = 20
        assert scores[0] < scores[1] < scores[2]

    def test_score_batch(self):
        """AC-FEAT-001-005: Batch scoring adds initial_score to all practices."""
        # Given: List of 10 practices without scores
        practices = [
            ApifyGoogleMapsResult(
                place_id=f"ChIJ{i}",
                practice_name=f"Vet {i}",
                address=f"{i} St",
                website=f"https://vet{i}.com",
                google_review_count=10 + i * 10,
                google_rating=min(3.5 + i * 0.2, 5.0),
                permanently_closed=False,
            )
            for i in range(10)
        ]

        scorer = InitialScorer()

        # When: Batch scoring
        scored_practices = scorer.score_batch(practices)

        # Then: All practices have scores in 0-25 range
        assert len(scored_practices) == 10
        assert all(hasattr(p, "initial_score") for p in scored_practices)
        assert all(0 <= p.initial_score <= 25 for p in scored_practices)

        # Original data not modified (except score added)
        for i, practice in enumerate(scored_practices):
            assert practice.place_id == f"ChIJ{i}"
            assert practice.google_review_count == 10 + i * 10
