"""
Unit tests for ApifyClient (FEAT-001).

Tests scraping, result parsing, error handling, and retry logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from pydantic import ValidationError

from src.scrapers.apify_client import ApifyClient
from src.models.apify_models import ApifyGoogleMapsResult


class TestApifyClient:
    """Test ApifyClient scraping functionality."""

    def test_run_google_maps_scraper_success(self, mock_apify_response):
        """AC-FEAT-001-001: Successful Google Maps scraping via Apify."""
        # Given: Valid Apify client and search parameters
        with patch("src.scrapers.apify_client.ApifyClient._get_apify_client") as mock_get_client:
            mock_client = Mock()
            mock_actor = Mock()
            mock_actor.call.return_value = mock_apify_response
            mock_client.actor.return_value = mock_actor
            mock_get_client.return_value = mock_client

            apify_client = ApifyClient(api_key="apify_api_test123")

            # When: Running Google Maps scraper
            result = apify_client.run_google_maps_scraper(
                search_queries=["veterinary clinic in Boston, MA"],
                max_results=50
            )

            # Then: Actor called with correct parameters
            mock_actor.call.assert_called_once()
            call_args = mock_actor.call.call_args
            assert "searchStringsArray" in call_args[1]["run_input"]
            assert call_args[1]["run_input"]["searchStringsArray"] == ["veterinary clinic in Boston, MA"]
            assert call_args[1]["run_input"]["maxCrawledPlacesPerSearch"] == 50

            # And: Returns run_id
            assert result == "run_test123"

    def test_run_google_maps_scraper_retry_on_failure(self):
        """AC-FEAT-001-012: Retry Apify API failures with exponential backoff."""
        # Given: Apify client that fails twice then succeeds
        with patch("src.scrapers.apify_client.ApifyClient._get_apify_client") as mock_get_client:
            mock_client = Mock()
            mock_actor = Mock()

            # First 2 calls raise error, 3rd succeeds
            mock_actor.call.side_effect = [
                Exception("Apify API error"),
                Exception("Apify API error"),
                {"id": "run_success", "status": "RUNNING", "defaultDatasetId": "dataset_123"}
            ]

            mock_client.actor.return_value = mock_actor
            mock_get_client.return_value = mock_client

            apify_client = ApifyClient(api_key="apify_api_test123")

            # When: Running scraper with retries
            result = apify_client.run_google_maps_scraper(
                search_queries=["veterinary clinic in Boston, MA"],
                max_results=50
            )

            # Then: Retried 3 times total
            assert mock_actor.call.call_count == 3

            # And: Returns run_id from successful attempt
            assert result == "run_success"

    def test_wait_for_results_success(self, mock_apify_response):
        """AC-FEAT-001-001: Wait for actor run to complete successfully."""
        # Given: Actor run that transitions from RUNNING to SUCCEEDED
        with patch("src.scrapers.apify_client.ApifyClient._get_apify_client") as mock_get_client:
            with patch("time.sleep"):  # Mock sleep to speed up test
                mock_client = Mock()
                mock_run = Mock()

                # Simulate status progression: RUNNING → RUNNING → SUCCEEDED
                mock_run.get.side_effect = [
                    {"status": "RUNNING"},
                    {"status": "RUNNING"},
                    {"status": "SUCCEEDED", "defaultDatasetId": "dataset_test456"}
                ]

                mock_client.run.return_value = mock_run
                mock_get_client.return_value = mock_client

                apify_client = ApifyClient(api_key="apify_api_test123")

                # When: Waiting for results
                dataset_id = apify_client.wait_for_results("run_test123")

                # Then: Polled until SUCCEEDED
                assert mock_run.get.call_count == 3

                # And: Returns dataset_id
                assert dataset_id == "dataset_test456"

    def test_wait_for_results_timeout(self):
        """AC-FEAT-001-013: Timeout if actor run exceeds 600 seconds."""
        # Given: Actor run stuck in RUNNING status
        with patch("src.scrapers.apify_client.ApifyClient._get_apify_client") as mock_get_client:
            with patch("time.sleep"):
                with patch("time.time") as mock_time:
                    # Simulate time passing: 0s, 10s, 20s, ... 610s (timeout)
                    mock_time.side_effect = [0, 10, 20, 30, 40, 50, 60, 610]

                    mock_client = Mock()
                    mock_run = Mock()
                    mock_run.get.return_value = {"status": "RUNNING"}
                    mock_client.run.return_value = mock_run
                    mock_get_client.return_value = mock_client

                    apify_client = ApifyClient(api_key="apify_api_test123")

                    # When/Then: Timeout error raised
                    with pytest.raises(TimeoutError) as exc_info:
                        apify_client.wait_for_results("run_test123", timeout=600)

                    # And: Error message contains run_id
                    assert "run_test123" in str(exc_info.value)

    def test_parse_results_valid_data(self, valid_practices_data):
        """AC-FEAT-001-001: Parse valid Apify dataset into Pydantic models."""
        # Given: Apify client and dataset with valid practices
        with patch("src.scrapers.apify_client.ApifyClient._get_apify_client") as mock_get_client:
            mock_client = Mock()
            mock_dataset = Mock()
            mock_dataset.iterate_items.return_value = iter(valid_practices_data)
            mock_client.dataset.return_value = mock_dataset
            mock_get_client.return_value = mock_client

            apify_client = ApifyClient(api_key="apify_api_test123")

            # When: Parsing results
            results = apify_client.parse_results("dataset_test456")

            # Then: Returns list of Pydantic models
            assert len(results) == 10
            assert all(isinstance(r, ApifyGoogleMapsResult) for r in results)

            # And: All required fields present
            assert results[0].place_id == "ChIJtest0"
            assert results[0].practice_name == "Test Vet Clinic 0"
            assert results[0].address == "0 Test St, Test City, CA 90001"

    def test_parse_results_invalid_data(self, invalid_practice_data):
        """AC-FEAT-001-016: Handle invalid data with validation errors."""
        # Given: Dataset with invalid practice (missing Place ID)
        with patch("src.scrapers.apify_client.ApifyClient._get_apify_client") as mock_get_client:
            mock_client = Mock()
            mock_dataset = Mock()
            mock_dataset.iterate_items.return_value = iter([invalid_practice_data])
            mock_client.dataset.return_value = mock_dataset
            mock_get_client.return_value = mock_client

            apify_client = ApifyClient(api_key="apify_api_test123")

            # When/Then: Validation error raised
            with pytest.raises(ValidationError) as exc_info:
                apify_client.parse_results("dataset_test456")

            # And: Error message contains field name
            error_str = str(exc_info.value).lower()
            assert "place" in error_str and "id" in error_str

    def test_apify_client_missing_api_key(self):
        """AC-FEAT-001-018: Clear error when API key missing."""
        # Given: No API key provided
        # When/Then: ValueError raised with helpful message
        with pytest.raises(ValueError) as exc_info:
            ApifyClient(api_key="")

        # And: Error message mentions API key
        error_msg = str(exc_info.value).lower()
        assert "api" in error_msg and "key" in error_msg


# Fixtures for test data
@pytest.fixture
def mock_apify_response():
    """Fixture providing mock Apify API response."""
    return {
        "id": "run_test123",
        "status": "RUNNING",
        "defaultDatasetId": "dataset_test456"
    }


@pytest.fixture
def valid_practices_data():
    """Fixture providing valid Google Maps practice data."""
    return [
        {
            "placeId": f"ChIJtest{i}",
            "title": f"Test Vet Clinic {i}",
            "address": f"{i} Test St, Test City, CA 90001",
            "phone": f"555-000-{i:04d}",
            "website": f"https://testvet{i}.com",
            "totalScore": 4.5,
            "reviewsCount": 50 + i * 10,
            "categoryName": "Veterinarian",
            "permanentlyClosed": False,
            "temporarilyClosed": False,
            "postalCode": "90001"
        }
        for i in range(10)
    ]


@pytest.fixture
def invalid_practice_data():
    """Fixture providing invalid practice data (missing Place ID)."""
    return {
        "title": "Test Vet Without Place ID",
        "address": "123 Test St",
        "phone": "555-0000",
        "website": "https://test.com",
        "totalScore": 4.5,
        "reviewsCount": 50
    }
