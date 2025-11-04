"""
Unit tests for NotionMapper (FEAT-001) - Enabled version.

Tests the transformation of VeterinaryPractice models to Notion API format.
TDD GREEN phase - all tests enabled.

Reference: AC-FEAT-001-010 (Notion Schema Compliance)
"""

import pytest
from typing import Dict, Any

from src.integrations.notion_mapper import NotionMapper
from src.models.apify_models import VeterinaryPractice


@pytest.fixture
def sample_practice():
    """Create a complete VeterinaryPractice instance for testing."""
    return VeterinaryPractice(
        place_id="ChIJN1t_tDeuEmsRUsoyG83frY4",
        practice_name="Boston Veterinary Clinic",
        address="123 Main St, Boston, MA 02101",
        phone="+16175551234",
        website="https://bostonvetclinic.com",
        google_rating=4.7,
        google_review_count=245,
        business_categories=["Veterinarian", "Pet Store"],
        postal_code="02101",
        permanently_closed=False,
        initial_score=25,
        priority_tier="Hot",
        first_scraped_date="2025-11-03T20:00:00Z",
    )


@pytest.fixture
def minimal_practice():
    """Create a minimal VeterinaryPractice with only required fields."""
    return VeterinaryPractice(
        place_id="ChIJMinimal123456",
        practice_name="Minimal Vet",
        address="456 Oak Ave, Cambridge, MA 02138",
        phone=None,
        website=None,
        google_rating=None,
        google_review_count=None,
        business_categories=[],
        postal_code=None,
        permanently_closed=False,
        initial_score=10,
        priority_tier="Cold",
        first_scraped_date=None,
    )


class TestNotionMapperFieldMapping:
    """Test individual field transformations to Notion properties."""

    def test_map_place_id_to_title_property(self, sample_practice):
        """AC-FEAT-001-010: Place ID should map to Title property."""
        mapper = NotionMapper(database_id="test_db_id")
        properties = mapper.map_to_notion_properties(sample_practice)

        assert "Place ID" in properties
        assert properties["Place ID"]["title"][0]["text"]["content"] == sample_practice.place_id

    def test_map_business_name_to_rich_text(self, sample_practice):
        """AC-FEAT-001-010: Business Name should map to rich_text property."""
        mapper = NotionMapper(database_id="test_db_id")
        properties = mapper.map_to_notion_properties(sample_practice)

        assert "Business Name" in properties
        assert properties["Business Name"]["rich_text"][0]["text"]["content"] == sample_practice.practice_name

    def test_map_address_to_rich_text(self, sample_practice):
        """AC-FEAT-001-010: Address should map to rich_text property."""
        mapper = NotionMapper(database_id="test_db_id")
        properties = mapper.map_to_notion_properties(sample_practice)

        assert "Address" in properties
        assert properties["Address"]["rich_text"][0]["text"]["content"] == sample_practice.address

    def test_map_phone_to_phone_number_property(self, sample_practice):
        """AC-FEAT-001-010: Phone should map to phone_number property (E.164 format)."""
        mapper = NotionMapper(database_id="test_db_id")
        properties = mapper.map_to_notion_properties(sample_practice)

        assert "Phone" in properties
        assert properties["Phone"]["phone_number"] == sample_practice.phone

    def test_map_website_to_url_property(self, sample_practice):
        """AC-FEAT-001-010: Website should map to url property."""
        mapper = NotionMapper(database_id="test_db_id")
        properties = mapper.map_to_notion_properties(sample_practice)

        assert "Website" in properties
        assert properties["Website"]["url"] == sample_practice.website

    def test_map_review_count_to_number_property(self, sample_practice):
        """AC-FEAT-001-010: Review Count should map to number property."""
        mapper = NotionMapper(database_id="test_db_id")
        properties = mapper.map_to_notion_properties(sample_practice)

        assert "Review Count" in properties
        assert properties["Review Count"]["number"] == sample_practice.google_review_count

    def test_map_star_rating_to_number_property(self, sample_practice):
        """AC-FEAT-001-010: Star Rating should map to number property."""
        mapper = NotionMapper(database_id="test_db_id")
        properties = mapper.map_to_notion_properties(sample_practice)

        assert "Star Rating" in properties
        assert properties["Star Rating"]["number"] == 4.7  # Already rounded in fixture

    def test_map_initial_score_to_number_property(self, sample_practice):
        """AC-FEAT-001-010: Initial Score should map to number property."""
        mapper = NotionMapper(database_id="test_db_id")
        properties = mapper.map_to_notion_properties(sample_practice)

        assert "Initial Score" in properties
        assert properties["Initial Score"]["number"] == sample_practice.initial_score

    def test_map_status_to_select_property(self, sample_practice):
        """AC-FEAT-001-010: Status should default to "New Lead" select property."""
        mapper = NotionMapper(database_id="test_db_id")
        properties = mapper.map_to_notion_properties(sample_practice)

        assert "Status" in properties
        assert properties["Status"]["select"]["name"] == "New Lead"


class TestNotionMapperNullHandling:
    """Test handling of null/optional fields."""

    def test_null_phone_maps_to_null(self, minimal_practice):
        """AC-FEAT-001-010: Null phone should map to null, not empty string."""
        mapper = NotionMapper(database_id="test_db_id")
        properties = mapper.map_to_notion_properties(minimal_practice)

        assert "Phone" in properties
        assert properties["Phone"]["phone_number"] is None

    def test_null_website_maps_to_null(self, minimal_practice):
        """AC-FEAT-001-010: Null website should map to null."""
        mapper = NotionMapper(database_id="test_db_id")
        properties = mapper.map_to_notion_properties(minimal_practice)

        assert "Website" in properties
        assert properties["Website"]["url"] is None

    def test_null_rating_maps_to_null(self, minimal_practice):
        """AC-FEAT-001-010: Null rating should map to null."""
        mapper = NotionMapper(database_id="test_db_id")
        properties = mapper.map_to_notion_properties(minimal_practice)

        assert "Star Rating" in properties
        assert properties["Star Rating"]["number"] is None

    def test_null_review_count_maps_to_null(self, minimal_practice):
        """AC-FEAT-001-010: Null review count should map to null."""
        mapper = NotionMapper(database_id="test_db_id")
        properties = mapper.map_to_notion_properties(minimal_practice)

        assert "Review Count" in properties
        assert properties["Review Count"]["number"] is None


class TestNotionMapperPagePayload:
    """Test full Notion API page payload creation."""

    def test_create_page_payload_structure(self, sample_practice):
        """Test that full page payload has correct structure for Notion API."""
        mapper = NotionMapper(database_id="test_db_123")
        payload = mapper.create_page_payload(sample_practice)

        assert "parent" in payload
        assert "database_id" in payload["parent"]
        assert payload["parent"]["database_id"] == "test_db_123"
        assert "properties" in payload

    def test_create_page_payload_has_all_required_properties(self, sample_practice):
        """Test that payload includes all 9 required properties from AC-FEAT-001-010."""
        mapper = NotionMapper(database_id="test_db_123")
        payload = mapper.create_page_payload(sample_practice)
        properties = payload["properties"]

        required_properties = [
            "Place ID",
            "Business Name",
            "Address",
            "Phone",
            "Website",
            "Review Count",
            "Star Rating",
            "Initial Score",
            "Status",
        ]

        for prop in required_properties:
            assert prop in properties, f"Missing required property: {prop}"

    def test_create_page_payload_with_minimal_data(self, minimal_practice):
        """Test that payload works with minimal data (nulls for optional fields)."""
        mapper = NotionMapper(database_id="test_db_123")
        payload = mapper.create_page_payload(minimal_practice)

        # Should not raise error with null values
        assert payload is not None
        assert "properties" in payload


class TestNotionMapperDatabaseId:
    """Test database ID handling."""

    def test_mapper_stores_database_id(self):
        """Test that NotionMapper stores database_id for use in page payloads."""
        mapper = NotionMapper(database_id="my_db_id_123")
        assert mapper.database_id == "my_db_id_123"

    def test_mapper_uses_database_id_in_payload(self, sample_practice):
        """Test that mapper uses stored database_id in page payloads."""
        mapper = NotionMapper(database_id="xyz_db")
        payload = mapper.create_page_payload(sample_practice)

        assert payload["parent"]["database_id"] == "xyz_db"


class TestNotionMapperEdgeCases:
    """Test edge cases and data quality."""

    def test_rating_with_high_precision(self):
        """Test that ratings with many decimals are formatted correctly."""
        practice = VeterinaryPractice(
            place_id="ChIJTest",
            practice_name="Test",
            address="123 Test St",
            google_rating=4.73333333,
            initial_score=10,
        )

        mapper = NotionMapper(database_id="test_db")
        properties = mapper.map_to_notion_properties(practice)

        # Should be rounded to 1 decimal place
        assert properties["Star Rating"]["number"] == 4.7
