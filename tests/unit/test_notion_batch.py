"""
Unit tests for NotionBatchUpserter (FEAT-001).

Tests batch operations, de-duplication, retry logic, and error handling for Notion uploads.
Follows TDD RED-GREEN-REFACTOR cycle.

References:
- AC-FEAT-001-006: Batch Upsert
- AC-FEAT-001-008: Within-batch de-duplication
- AC-FEAT-001-009: Cross-batch de-duplication
- AC-FEAT-001-014: Retry on 429
- AC-FEAT-001-017: Partial batch failure
- AC-FEAT-001-026: Rate limiting
"""

import pytest
import time
from unittest.mock import Mock, patch, call, MagicMock
from notion_client import APIResponseError

from src.models.apify_models import VeterinaryPractice
from src.integrations.notion_batch import NotionBatchUpserter, deduplicate_by_place_id


@pytest.fixture
def sample_practices():
    """Create 10 unique VeterinaryPractice instances for testing."""
    practices = []
    for i in range(10):
        practices.append(
            VeterinaryPractice(
                place_id=f"ChIJPlace{i:03d}",
                practice_name=f"Vet Clinic {i}",
                address=f"{i}00 Main St, Boston, MA 02101",
                phone=f"+1617555{i:04d}",
                website=f"https://vet{i}.com",
                google_rating=4.5,
                google_review_count=100 + i * 10,
                business_categories=["Veterinarian"],
                postal_code="02101",
                permanently_closed=False,
                initial_score=20,
                priority_tier="Warm",
            )
        )
    return practices


@pytest.fixture
def duplicate_practices():
    """Create practices with 3 duplicate Place IDs."""
    practices = []

    # First occurrence of duplicate Place ID
    practices.append(
        VeterinaryPractice(
            place_id="ChIJDuplicate001",
            practice_name="First Occurrence",
            address="100 First St",
            initial_score=25,
        )
    )

    # 5 unique practices
    for i in range(2, 7):
        practices.append(
            VeterinaryPractice(
                place_id=f"ChIJUnique{i:03d}",
                practice_name=f"Unique Vet {i}",
                address=f"{i}00 Main St",
                initial_score=20,
            )
        )

    # Second occurrence of duplicate (should be removed)
    practices.append(
        VeterinaryPractice(
            place_id="ChIJDuplicate001",
            practice_name="Second Occurrence (DUPLICATE)",
            address="200 Second St",
            initial_score=15,
        )
    )

    # More unique practices
    for i in range(8, 10):
        practices.append(
            VeterinaryPractice(
                place_id=f"ChIJUnique{i:03d}",
                practice_name=f"Unique Vet {i}",
                address=f"{i}00 Main St",
                initial_score=20,
            )
        )

    # Third occurrence of duplicate (should be removed)
    practices.append(
        VeterinaryPractice(
            place_id="ChIJDuplicate001",
            practice_name="Third Occurrence (DUPLICATE)",
            address="300 Third St",
            initial_score=10,
        )
    )

    return practices  # 10 total: 1 duplicate (3 occurrences) + 7 unique = 8 after deduplication


class TestDeduplicationWithinBatch:
    """Test de-duplication logic within a single batch (AC-FEAT-001-008)."""

    def test_deduplicate_by_place_id_removes_duplicates(self, duplicate_practices):
        """
        AC-FEAT-001-008: De-duplicate within batch.

        Given 10 practices with 3 duplicate Place IDs (1 ID appears 3 times)
        When deduplicate_by_place_id is called
        Then it should return 8 unique practices (7 unique + 1 kept from duplicates)
        """
        result = deduplicate_by_place_id(duplicate_practices)

        assert len(result) == 8, f"Expected 8 unique practices, got {len(result)}"

        # Check all Place IDs are unique
        place_ids = [p.place_id for p in result]
        assert len(place_ids) == len(set(place_ids)), "Result should have no duplicate Place IDs"

    def test_deduplicate_preserves_first_occurrence(self, duplicate_practices):
        """
        AC-FEAT-001-008: Preserve first occurrence of duplicates.

        Given duplicates with different practice names
        When deduplicate_by_place_id is called
        Then it should keep the first occurrence only
        """
        result = deduplicate_by_place_id(duplicate_practices)

        # Find the practice with duplicate Place ID
        duplicate_practice = next(p for p in result if p.place_id == "ChIJDuplicate001")

        # Should be "First Occurrence", not "Second" or "Third"
        assert duplicate_practice.practice_name == "First Occurrence"
        assert duplicate_practice.initial_score == 25  # First occurrence's score

    def test_deduplicate_with_no_duplicates(self, sample_practices):
        """
        AC-FEAT-001-008: Handle practices with no duplicates.

        Given 10 practices with all unique Place IDs
        When deduplicate_by_place_id is called
        Then it should return all 10 practices unchanged
        """
        result = deduplicate_by_place_id(sample_practices)

        assert len(result) == 10
        assert result == sample_practices  # Order and content preserved

    def test_deduplicate_with_empty_list(self):
        """
        Edge case: Empty list should return empty list.
        """
        result = deduplicate_by_place_id([])

        assert result == []


class TestCheckExistingPlaceIds:
    """Test querying existing Place IDs from Notion (AC-FEAT-001-009)."""

    @patch('src.integrations.notion_batch.Client')
    def test_check_existing_place_ids_returns_set(self, mock_notion_client):
        """
        AC-FEAT-001-009: Query existing Place IDs from Notion database.

        Given Notion database contains 5 practices
        When check_existing_place_ids is called
        Then it should return set of 5 Place IDs
        """
        # Mock Notion API response (paginated query)
        mock_client_instance = mock_notion_client.return_value
        mock_client_instance.databases.query.return_value = {
            "results": [
                {"properties": {"Place ID": {"title": [{"text": {"content": "ChIJExisting001"}}]}}},
                {"properties": {"Place ID": {"title": [{"text": {"content": "ChIJExisting002"}}]}}},
                {"properties": {"Place ID": {"title": [{"text": {"content": "ChIJExisting003"}}]}}},
                {"properties": {"Place ID": {"title": [{"text": {"content": "ChIJExisting004"}}]}}},
                {"properties": {"Place ID": {"title": [{"text": {"content": "ChIJExisting005"}}]}}},
            ],
            "has_more": False,
        }

        upserter = NotionBatchUpserter(
            api_key="test_key",
            database_id="test_db",
            batch_size=10
        )

        existing_ids = upserter.check_existing_place_ids()

        assert len(existing_ids) == 5
        assert "ChIJExisting001" in existing_ids
        assert "ChIJExisting005" in existing_ids
        assert isinstance(existing_ids, set)

    @patch('src.integrations.notion_batch.Client')
    def test_check_existing_place_ids_handles_pagination(self, mock_notion_client):
        """
        AC-FEAT-001-009: Handle Notion API pagination (100 results per page).

        Given Notion database contains 150 practices (2 pages)
        When check_existing_place_ids is called
        Then it should query all pages and return all Place IDs
        """
        mock_client_instance = mock_notion_client.return_value

        # First page: 100 results, has_more=True
        page1_results = [
            {"properties": {"Place ID": {"title": [{"text": {"content": f"ChIJPage1_{i:03d}"}}]}}}
            for i in range(100)
        ]

        # Second page: 50 results, has_more=False
        page2_results = [
            {"properties": {"Place ID": {"title": [{"text": {"content": f"ChIJPage2_{i:03d}"}}]}}}
            for i in range(50)
        ]

        mock_client_instance.databases.query.side_effect = [
            {"results": page1_results, "has_more": True, "next_cursor": "cursor_123"},
            {"results": page2_results, "has_more": False},
        ]

        upserter = NotionBatchUpserter(
            api_key="test_key",
            database_id="test_db",
            batch_size=10
        )

        existing_ids = upserter.check_existing_place_ids()

        assert len(existing_ids) == 150
        assert mock_client_instance.databases.query.call_count == 2


class TestBatchUpsertCreation:
    """Test batch page creation in Notion (AC-FEAT-001-006)."""

    @patch('src.integrations.notion_batch.Client')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_upsert_batch_creates_pages(self, mock_sleep, mock_notion_client, sample_practices):
        """
        AC-FEAT-001-006: Batch create pages in Notion.

        Given 10 practices (all new)
        When upsert_batch is called
        Then 10 Notion pages should be created
        """
        mock_client_instance = mock_notion_client.return_value

        # Mock empty existing Place IDs (all practices are new)
        mock_client_instance.databases.query.return_value = {
            "results": [],
            "has_more": False,
        }

        # Mock successful page creation
        mock_client_instance.pages.create.return_value = {"id": "page_123"}

        upserter = NotionBatchUpserter(
            api_key="test_key",
            database_id="test_db",
            batch_size=10
        )

        result = upserter.upsert_batch(sample_practices)

        assert result["created"] == 10
        assert result["skipped"] == 0
        assert result["failed"] == 0
        assert mock_client_instance.pages.create.call_count == 10


class TestBatchRateLimiting:
    """Test rate limiting between batches (AC-FEAT-001-026)."""

    @patch('src.integrations.notion_batch.Client')
    @patch('time.sleep')
    def test_upsert_batch_rate_limiting(self, mock_sleep, mock_notion_client):
        """
        AC-FEAT-001-026: Rate limit batches with 3.5s delay.

        Given 30 practices with batch_size=10
        When upsert_batch is called
        Then it should create 3 batches with 3.5s sleep between batches (but not after last batch)
        """
        # Create 30 practices
        practices = [
            VeterinaryPractice(
                place_id=f"ChIJPlace{i:03d}",
                practice_name=f"Vet {i}",
                address=f"{i} Main St",
                initial_score=20,
            )
            for i in range(30)
        ]

        mock_client_instance = mock_notion_client.return_value
        mock_client_instance.databases.query.return_value = {"results": [], "has_more": False}
        mock_client_instance.pages.create.return_value = {"id": "page_123"}

        upserter = NotionBatchUpserter(
            api_key="test_key",
            database_id="test_db",
            batch_size=10,
            rate_limit_delay=3.5
        )

        result = upserter.upsert_batch(practices)

        # Should process 3 batches (30 practices / 10 per batch)
        assert result["created"] == 30

        # Should sleep 2 times (after batch 1, after batch 2, but NOT after batch 3)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_has_calls([call(3.5), call(3.5)])


class TestSkipExistingRecords:
    """Test skipping duplicate Place IDs already in Notion (AC-FEAT-001-009)."""

    @patch('src.integrations.notion_batch.Client')
    @patch('time.sleep')
    def test_upsert_batch_skips_existing(self, mock_sleep, mock_notion_client):
        """
        AC-FEAT-001-009: Skip practices already in Notion database.

        Given 10 practices (5 existing in Notion, 5 new)
        When upsert_batch is called
        Then only 5 new pages should be created, 5 should be skipped
        """
        practices = [
            VeterinaryPractice(
                place_id=f"ChIJPlace{i:03d}",
                practice_name=f"Vet {i}",
                address=f"{i} Main St",
                initial_score=20,
            )
            for i in range(10)
        ]

        mock_client_instance = mock_notion_client.return_value

        # Mock existing Place IDs (first 5 practices)
        mock_client_instance.databases.query.return_value = {
            "results": [
                {"properties": {"Place ID": {"title": [{"text": {"content": f"ChIJPlace{i:03d}"}}]}}}
                for i in range(5)
            ],
            "has_more": False,
        }

        mock_client_instance.pages.create.return_value = {"id": "page_123"}

        upserter = NotionBatchUpserter(
            api_key="test_key",
            database_id="test_db",
            batch_size=10
        )

        result = upserter.upsert_batch(practices)

        assert result["created"] == 5  # Only new practices
        assert result["skipped"] == 5  # Existing practices
        assert result["failed"] == 0


class TestRetryOn429:
    """Test retry logic on Notion API 429 rate limit errors (AC-FEAT-001-014)."""

    @patch('src.integrations.notion_batch.Client')
    def test_upsert_batch_retry_on_429(self, mock_notion_client):
        """
        AC-FEAT-001-014: Retry with exponential backoff on 429 errors.

        Given Notion API returns 429 on first 2 attempts
        When upsert_batch creates a page
        Then it should retry with exponential backoff and succeed on 3rd attempt
        """
        mock_client_instance = mock_notion_client.return_value
        mock_client_instance.databases.query.return_value = {"results": [], "has_more": False}

        # First 2 calls raise 429, 3rd+ succeeds
        # APIResponseError requires: response, message, code
        mock_response_429 = Mock(status_code=429, json=lambda: {"code": "rate_limited"})

        def mock_create_with_retry(*args, **kwargs):
            if not hasattr(mock_create_with_retry, 'call_count'):
                mock_create_with_retry.call_count = 0
            mock_create_with_retry.call_count += 1

            if mock_create_with_retry.call_count <= 2:
                raise APIResponseError(response=mock_response_429, message="Rate limited", code="rate_limited")
            return {"id": "page_success"}

        mock_client_instance.pages.create.side_effect = mock_create_with_retry

        practice = VeterinaryPractice(
            place_id="ChIJTest",
            practice_name="Test Vet",
            address="123 Test St",
            initial_score=20,
        )

        upserter = NotionBatchUpserter(
            api_key="test_key",
            database_id="test_db",
            batch_size=10
        )

        result = upserter.upsert_batch([practice])

        # Should succeed after retries
        assert result["created"] == 1, f"Expected 1 created, got: {result}"
        assert result["failed"] == 0, f"Expected 0 failed, got: {result}"

        # Should have called create 3 times (2 failures + 1 success)
        actual_calls = mock_client_instance.pages.create.call_count
        assert actual_calls == 3, f"Expected 3 calls, got {actual_calls}"


class TestPartialBatchFailure:
    """Test handling of partial batch failures (AC-FEAT-001-017)."""

    @patch('src.integrations.notion_batch.Client')
    @patch('time.sleep')
    def test_upsert_batch_partial_failure(self, mock_sleep, mock_notion_client):
        """
        AC-FEAT-001-017: Continue processing batch despite individual failures.

        Given 10 practices where 2 fail with 400 validation errors
        When upsert_batch is called
        Then 8 pages should be created and 2 errors should be logged
        """
        practices = [
            VeterinaryPractice(
                place_id=f"ChIJPlace{i:03d}",
                practice_name=f"Vet {i}",
                address=f"{i} Main St",
                initial_score=20,
            )
            for i in range(10)
        ]

        mock_client_instance = mock_notion_client.return_value
        mock_client_instance.databases.query.return_value = {"results": [], "has_more": False}

        # Mock failures for practices 2 and 7 (400 validation errors)
        def mock_create_side_effect(*args, **kwargs):
            if not hasattr(mock_create_side_effect, 'call_count'):
                mock_create_side_effect.call_count = 0
            mock_create_side_effect.call_count += 1

            if mock_create_side_effect.call_count in [3, 8]:  # 3rd and 8th calls fail
                raise APIResponseError(
                    response=Mock(status_code=400, json=lambda: {"code": "validation_error"}),
                    message="Validation error",
                    code="validation_error"
                )
            return {"id": f"page_{mock_create_side_effect.call_count}"}

        mock_client_instance.pages.create.side_effect = mock_create_side_effect

        upserter = NotionBatchUpserter(
            api_key="test_key",
            database_id="test_db",
            batch_size=10
        )

        result = upserter.upsert_batch(practices)

        assert result["created"] == 8
        assert result["failed"] == 2
        assert len(result["errors"]) == 2

        # Check error details
        assert all("place_id" in error for error in result["errors"])
        assert all("error" in error for error in result["errors"])


class TestBatchUpserterInitialization:
    """Test NotionBatchUpserter initialization."""

    @patch('src.integrations.notion_batch.Client')
    def test_upserter_initialization(self, mock_notion_client):
        """Test that NotionBatchUpserter initializes with correct parameters."""
        upserter = NotionBatchUpserter(
            api_key="test_api_key",
            database_id="test_db_id",
            batch_size=15,
            rate_limit_delay=5.0
        )

        assert upserter.database_id == "test_db_id"
        assert upserter.batch_size == 15
        assert upserter.rate_limit_delay == 5.0

        # Should initialize Notion client with API key
        mock_notion_client.assert_called_once_with(auth="test_api_key")

    @patch('src.integrations.notion_batch.Client')
    def test_upserter_default_parameters(self, mock_notion_client):
        """Test that NotionBatchUpserter uses correct default parameters."""
        upserter = NotionBatchUpserter(
            api_key="test_api_key",
            database_id="test_db_id"
        )

        # Default batch_size should be 10
        assert upserter.batch_size == 10

        # Default rate_limit_delay should be 3.5s (2.86 req/s)
        assert upserter.rate_limit_delay == 3.5
