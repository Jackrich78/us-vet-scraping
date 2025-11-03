"""
Unit tests for DataFilter (FEAT-001).

Tests filtering logic for website, reviews, and open status.
"""

import pytest
from src.processing.data_filter import DataFilter
from src.models.apify_models import ApifyGoogleMapsResult


class TestDataFilter:
    """Test DataFilter class functionality."""

    def test_filter_has_website_excludes_missing(self, practices_with_mixed_websites):
        """AC-FEAT-001-002: Exclude practices without website."""
        # Given: Practices with mixed website values (valid, None, empty)
        filter_service = DataFilter()

        # When: Applying website filter
        filtered = filter_service.filter_has_website(practices_with_mixed_websites)

        # Then: Only practices with valid websites remain
        assert len(filtered) == 3
        assert all(p.website for p in filtered)
        assert all(p.website != "" for p in filtered)

    def test_filter_has_website_excludes_empty(self):
        """AC-FEAT-001-002: Exclude practices with empty string website."""
        # Given: Practices with empty string websites
        practices = [
            ApifyGoogleMapsResult(
                place_id="1",
                practice_name="Test 1",
                address="123 St",
                website="https://valid.com",
            ),
            ApifyGoogleMapsResult(
                place_id="2",
                practice_name="Test 2",
                address="456 St",
                website="",  # Empty string
            ),
        ]

        filter_service = DataFilter()

        # When: Applying website filter
        filtered = filter_service.filter_has_website(practices)

        # Then: Empty string websites excluded
        assert len(filtered) == 1
        assert filtered[0].place_id == "1"

    def test_filter_min_reviews_excludes_below_threshold(
        self, practices_with_varied_reviews
    ):
        """AC-FEAT-001-003: Exclude practices with <10 reviews."""
        # Given: Practices with 5, 8, 10, 12, 50, 100 reviews
        filter_service = DataFilter()

        # When: Applying min reviews filter with threshold=10
        filtered = filter_service.filter_min_reviews(
            practices_with_varied_reviews, min_reviews=10
        )

        # Then: Only practices with >=10 reviews remain
        assert len(filtered) == 4  # 10, 12, 50, 100
        assert all(p.google_review_count >= 10 for p in filtered)

    def test_filter_min_reviews_default_threshold(self, practices_with_varied_reviews):
        """AC-FEAT-001-003: Default threshold is 10 reviews."""
        # Given: Practices with varied review counts
        filter_service = DataFilter()

        # When: Applying filter without specifying threshold
        filtered = filter_service.filter_min_reviews(practices_with_varied_reviews)

        # Then: Default threshold of 10 is used
        assert len(filtered) == 4  # 10, 12, 50, 100
        assert all(p.google_review_count >= 10 for p in filtered)

    def test_filter_is_open_excludes_closed(self, practices_with_varied_status):
        """AC-FEAT-001-004: Exclude permanently closed, keep temporarily closed."""
        # Given: Practices with OPEN, CLOSED, TEMPORARILY_CLOSED status
        filter_service = DataFilter()

        # When: Applying open status filter
        filtered = filter_service.filter_is_open(practices_with_varied_status)

        # Then: Permanently closed excluded, temporarily closed included
        assert len(filtered) == 2
        assert all(not p.permanently_closed for p in filtered)

    def test_apply_all_filters_integration(self, mixed_quality_practices):
        """AC-FEAT-001-002, AC-FEAT-001-003, AC-FEAT-001-004: All filters together."""
        # Given: 20 practices with various quality issues
        filter_service = DataFilter()

        # When: Applying all filters together
        filtered = filter_service.apply_all_filters(mixed_quality_practices)

        # Then: Only practices passing all filters remain
        assert len(filtered) == 5

        # Verify each practice meets all criteria
        for practice in filtered:
            assert practice.website is not None
            assert practice.website != ""
            assert practice.google_review_count >= 10
            assert not practice.permanently_closed


# Fixtures for test data
@pytest.fixture
def practices_with_mixed_websites():
    """Fixture providing practices with various website states."""
    return [
        ApifyGoogleMapsResult(
            place_id="1",
            practice_name="Valid 1",
            address="1 St",
            website="https://valid1.com",
            google_review_count=20,
            permanently_closed=False,
        ),
        ApifyGoogleMapsResult(
            place_id="2",
            practice_name="Valid 2",
            address="2 St",
            website="https://valid2.com",
            google_review_count=20,
            permanently_closed=False,
        ),
        ApifyGoogleMapsResult(
            place_id="3",
            practice_name="Valid 3",
            address="3 St",
            website="https://valid3.com",
            google_review_count=20,
            permanently_closed=False,
        ),
        ApifyGoogleMapsResult(
            place_id="4",
            practice_name="No Website",
            address="4 St",
            website=None,
            google_review_count=20,
            permanently_closed=False,
        ),
        ApifyGoogleMapsResult(
            place_id="5",
            practice_name="Empty Website",
            address="5 St",
            website="",
            google_review_count=20,
            permanently_closed=False,
        ),
    ]


@pytest.fixture
def practices_with_varied_reviews():
    """Fixture providing practices with different review counts."""
    return [
        ApifyGoogleMapsResult(
            place_id="1",
            practice_name="5 Reviews",
            address="1 St",
            website="https://test.com",
            google_review_count=5,
            permanently_closed=False,
        ),
        ApifyGoogleMapsResult(
            place_id="2",
            practice_name="8 Reviews",
            address="2 St",
            website="https://test.com",
            google_review_count=8,
            permanently_closed=False,
        ),
        ApifyGoogleMapsResult(
            place_id="3",
            practice_name="10 Reviews",
            address="3 St",
            website="https://test.com",
            google_review_count=10,
            permanently_closed=False,
        ),
        ApifyGoogleMapsResult(
            place_id="4",
            practice_name="12 Reviews",
            address="4 St",
            website="https://test.com",
            google_review_count=12,
            permanently_closed=False,
        ),
        ApifyGoogleMapsResult(
            place_id="5",
            practice_name="50 Reviews",
            address="5 St",
            website="https://test.com",
            google_review_count=50,
            permanently_closed=False,
        ),
        ApifyGoogleMapsResult(
            place_id="6",
            practice_name="100 Reviews",
            address="6 St",
            website="https://test.com",
            google_review_count=100,
            permanently_closed=False,
        ),
    ]


@pytest.fixture
def practices_with_varied_status():
    """Fixture providing practices with different operational status."""
    return [
        ApifyGoogleMapsResult(
            place_id="1",
            practice_name="Open",
            address="1 St",
            website="https://test.com",
            google_review_count=20,
            permanently_closed=False,
            temporarily_closed=False,
        ),
        ApifyGoogleMapsResult(
            place_id="2",
            practice_name="Permanently Closed",
            address="2 St",
            website="https://test.com",
            google_review_count=20,
            permanently_closed=True,
            temporarily_closed=False,
        ),
        ApifyGoogleMapsResult(
            place_id="3",
            practice_name="Temporarily Closed",
            address="3 St",
            website="https://test.com",
            google_review_count=20,
            permanently_closed=False,
            temporarily_closed=True,
        ),
    ]


@pytest.fixture
def mixed_quality_practices():
    """Fixture providing 20 practices with various filter violations."""
    practices = []

    # 5 with no website (fail website filter)
    for i in range(5):
        practices.append(
            ApifyGoogleMapsResult(
                place_id=f"no_web_{i}",
                practice_name=f"No Website {i}",
                address=f"{i} St",
                website=None,
                google_review_count=50,
                permanently_closed=False,
            )
        )

    # 5 with <10 reviews (fail reviews filter)
    for i in range(5):
        practices.append(
            ApifyGoogleMapsResult(
                place_id=f"low_reviews_{i}",
                practice_name=f"Low Reviews {i}",
                address=f"{i} St",
                website="https://test.com",
                google_review_count=5,
                permanently_closed=False,
            )
        )

    # 5 permanently closed (fail status filter)
    for i in range(5):
        practices.append(
            ApifyGoogleMapsResult(
                place_id=f"closed_{i}",
                practice_name=f"Closed {i}",
                address=f"{i} St",
                website="https://test.com",
                google_review_count=50,
                permanently_closed=True,
            )
        )

    # 5 valid (pass all filters)
    for i in range(5):
        practices.append(
            ApifyGoogleMapsResult(
                place_id=f"valid_{i}",
                practice_name=f"Valid {i}",
                address=f"{i} St",
                website="https://valid.com",
                google_review_count=50,
                permanently_closed=False,
            )
        )

    return practices
