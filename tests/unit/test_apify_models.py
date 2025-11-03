"""
Unit tests for Apify data models (FEAT-001).

Tests validate Pydantic models for Google Maps scraping results with edge cases:
- Missing Place ID (requires composite key fallback)
- Null postal codes (parse from address)
- Invalid URLs (sanitization)
- Phone number normalization (E.164 format)
"""

import pytest
from pydantic import ValidationError
from src.models.apify_models import ApifyGoogleMapsResult, VeterinaryPractice


class TestApifyGoogleMapsResult:
    """Test ApifyGoogleMapsResult Pydantic model validation."""

    def test_valid_google_maps_result(self):
        """AC-FEAT-001-001: Parse valid Google Maps result with all fields."""
        # Given: Valid Apify API response data
        data = {
            "placeId": "ChIJXyz123ABC",
            "title": "Happy Paws Veterinary Clinic",
            "address": "123 Main St, Boston, MA 02101",
            "phone": "+1 617-555-0100",
            "website": "https://happypaws.com",
            "totalScore": 4.5,
            "reviewsCount": 150,
            "categoryName": "Veterinarian",
            "location": {"lat": 42.3601, "lng": -71.0589},
            "permanentlyClosed": False,
            "temporarilyClosed": False,
            "postalCode": "02101",
        }

        # When: Parsing into Pydantic model
        result = ApifyGoogleMapsResult(**data)

        # Then: All fields are correctly parsed and validated
        assert result.place_id == "ChIJXyz123ABC"
        assert result.practice_name == "Happy Paws Veterinary Clinic"
        assert result.address == "123 Main St, Boston, MA 02101"
        assert result.phone == "+16175550100"  # E.164 format (no spaces)
        assert result.website == "https://happypaws.com"
        assert result.google_rating == 4.5
        assert result.google_review_count == 150
        assert result.business_categories == ["Veterinarian"]
        assert result.postal_code == "02101"
        assert result.permanently_closed is False

    def test_missing_place_id_raises_validation_error(self):
        """AC-FEAT-001-027: Place ID is required field (fallback handled at service layer)."""
        # Given: Data without Place ID
        data = {
            "title": "Happy Paws Veterinary Clinic",
            "address": "123 Main St, Boston, MA 02101",
        }

        # When/Then: Validation error raised
        with pytest.raises(ValidationError) as exc_info:
            ApifyGoogleMapsResult(**data)

        # Check for either Python field name or API alias
        error_str = str(exc_info.value).lower()
        assert "place" in error_str and "id" in error_str

    def test_null_postal_code_parsed_from_address(self):
        """AC-FEAT-001-001: Parse postal code from address when null."""
        # Given: Data with null postalCode but address contains ZIP
        data = {
            "placeId": "ChIJXyz123ABC",
            "title": "Happy Paws Veterinary Clinic",
            "address": "123 Main St, Boston, MA 02101",
            "postalCode": None,
        }

        # When: Parsing into model
        result = ApifyGoogleMapsResult(**data)

        # Then: Postal code extracted from address
        assert result.postal_code == "02101"

    def test_invalid_url_sanitized_with_https(self):
        """AC-FEAT-001-030: URLs without protocol get https:// prefix."""
        # Given: Website URL without protocol
        data = {
            "placeId": "ChIJXyz123ABC",
            "title": "Happy Paws Veterinary Clinic",
            "address": "123 Main St, Boston, MA 02101",
            "website": "happypaws.com",
        }

        # When: Parsing into model
        result = ApifyGoogleMapsResult(**data)

        # Then: URL sanitized with https:// prefix
        assert result.website == "https://happypaws.com"

    def test_phone_normalized_to_e164(self):
        """AC-FEAT-001-010: Phone numbers normalized to E.164 format."""
        # Given: Phone in various formats
        test_cases = [
            ("(617) 555-0100", "+16175550100"),
            ("617-555-0100", "+16175550100"),
            ("617.555.0100", "+16175550100"),
            ("+1 617 555 0100", "+16175550100"),
        ]

        for input_phone, expected_e164 in test_cases:
            data = {
                "placeId": "ChIJXyz123ABC",
                "title": "Happy Paws Veterinary Clinic",
                "address": "123 Main St, Boston, MA 02101",
                "phone": input_phone,
            }

            # When: Parsing into model
            result = ApifyGoogleMapsResult(**data)

            # Then: Phone normalized to E.164
            assert result.phone == expected_e164, f"Failed for input: {input_phone}"

    def test_rating_range_validation(self):
        """AC-FEAT-001-029: Star rating must be 0.0-5.0."""
        # Given: Invalid rating (>5.0)
        data = {
            "placeId": "ChIJXyz123ABC",
            "title": "Happy Paws Veterinary Clinic",
            "address": "123 Main St, Boston, MA 02101",
            "totalScore": 6.0,  # Invalid
        }

        # When/Then: Validation error raised
        with pytest.raises(ValidationError) as exc_info:
            ApifyGoogleMapsResult(**data)

        # Check for validation error on rating field (either Python name or alias)
        error_str = str(exc_info.value).lower()
        assert ("rating" in error_str or "score" in error_str) and "5" in error_str

    def test_empty_category_defaults_to_list(self):
        """Handle missing or null category gracefully."""
        # Given: Data without category
        data = {
            "placeId": "ChIJXyz123ABC",
            "title": "Happy Paws Veterinary Clinic",
            "address": "123 Main St, Boston, MA 02101",
            "categoryName": None,
        }

        # When: Parsing into model
        result = ApifyGoogleMapsResult(**data)

        # Then: Category is empty list
        assert result.business_categories == []


class TestVeterinaryPractice:
    """Test VeterinaryPractice model with scoring."""

    def test_valid_practice_with_score(self):
        """AC-FEAT-001-005: Practice model with initial score (0-25)."""
        # Given: Filtered and scored practice data
        data = {
            "place_id": "ChIJXyz123ABC",
            "practice_name": "Happy Paws Veterinary Clinic",
            "address": "123 Main St, Boston, MA 02101",
            "phone": "+16175550100",
            "website": "https://happypaws.com",
            "google_rating": 4.5,
            "google_review_count": 150,
            "business_categories": ["Veterinarian"],
            "initial_score": 25,
            "priority_tier": "Hot",
            "postal_code": "02101",
            "permanently_closed": False,
        }

        # When: Creating practice model
        practice = VeterinaryPractice(**data)

        # Then: All fields validated
        assert practice.initial_score == 25
        assert practice.priority_tier == "Hot"

    def test_score_range_validation_max(self):
        """AC-FEAT-001-028: Initial score must be 0-25."""
        # Given: Score > 25
        data = {
            "place_id": "ChIJXyz123ABC",
            "practice_name": "Happy Paws Veterinary Clinic",
            "address": "123 Main St, Boston, MA 02101",
            "initial_score": 30,  # Invalid
        }

        # When/Then: Validation error raised
        with pytest.raises(ValidationError) as exc_info:
            VeterinaryPractice(**data)

        assert "initial_score" in str(exc_info.value).lower()

    def test_score_range_validation_min(self):
        """AC-FEAT-001-028: Initial score must be >= 0."""
        # Given: Score < 0
        data = {
            "place_id": "ChIJXyz123ABC",
            "practice_name": "Happy Paws Veterinary Clinic",
            "address": "123 Main St, Boston, MA 02101",
            "initial_score": -5,  # Invalid
        }

        # When/Then: Validation error raised
        with pytest.raises(ValidationError) as exc_info:
            VeterinaryPractice(**data)

        assert "initial_score" in str(exc_info.value).lower()

    def test_priority_tier_defaults_to_cold(self):
        """Priority tier defaults to 'Cold' if not provided."""
        # Given: Data without priority_tier
        data = {
            "place_id": "ChIJXyz123ABC",
            "practice_name": "Happy Paws Veterinary Clinic",
            "address": "123 Main St, Boston, MA 02101",
            "initial_score": 10,
        }

        # When: Creating practice model
        practice = VeterinaryPractice(**data)

        # Then: Default is 'Cold'
        assert practice.priority_tier == "Cold"
