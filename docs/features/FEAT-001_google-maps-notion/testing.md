# Testing Strategy
**Feature:** FEAT-001 - Google Maps Scraping & Notion Integration
**Date:** 2025-11-03
**Version:** 1.0

## Overview

This document defines the comprehensive testing strategy for the Google Maps scraping and Notion integration pipeline. Testing follows a three-tier approach: unit tests for individual components, integration tests for component interactions, and end-to-end tests for full pipeline validation.

## Testing Philosophy

**Test-Driven Development (TDD):** Write test stubs first during planning, implement tests before code, follow Red-Green-Refactor cycle.

**Coverage Goals:**
- Overall: 80%+ code coverage
- Critical paths (scraping, filtering, scoring, Notion upload): 95%+ coverage
- Error handling: 100% coverage (all retry/fallback logic)

**Mocking Strategy:**
- Mock all external APIs (Apify, Notion) to avoid costs and ensure test speed
- Use real data structures (Pydantic models) with fixture data
- Test actual HTTP clients with recorded responses (VCR.py) for integration tests

## Test Levels

### Level 1: Unit Tests

**Objective:** Validate individual components in isolation

**Scope:**
- ApifyClient methods (run_google_maps_scraper, wait_for_results, parse_results)
- DataFilter logic (filter_has_website, filter_min_reviews, filter_is_open)
- InitialScorer calculation (calculate_score, score_batch)
- NotionMapper transformations (map_to_notion_properties, create_page_payload)
- NotionBatchUpserter operations (deduplicate_by_place_id, upsert_batch)

**Tools:**
- pytest: Test framework
- unittest.mock: Mock external dependencies
- pytest-cov: Coverage reporting
- Pydantic: Data validation

**Files to Create:**
```
tests/unit/
├── test_apify_client.py (7 tests)
├── test_data_filter.py (6 tests)
├── test_initial_scorer.py (5 tests)
├── test_notion_mapper.py (5 tests)
└── test_notion_batch.py (8 tests)
```

### Level 2: Integration Tests

**Objective:** Validate component interactions and data flow

**Scope:**
- Apify scraping → Data filtering pipeline
- Filtering → Scoring → Notion mapping pipeline
- Notion batch operations with rate limiting
- Retry logic with transient failures
- End-to-end data transformation (Apify JSON → Notion payload)

**Tools:**
- pytest: Test framework
- pytest-mock: Enhanced mocking
- VCR.py: Record/replay HTTP interactions
- freezegun: Mock time.sleep for rate limiting tests

**Files to Create:**
```
tests/integration/
├── test_scraping_pipeline.py (5 tests)
├── test_notion_integration.py (6 tests)
└── test_retry_logic.py (4 tests)
```

### Level 3: End-to-End Tests

**Objective:** Validate full pipeline with real-world scenarios

**Scope:**
- Test mode (--test flag) with 10 practices
- Full pipeline execution (CLI → Apify → Filter → Score → Notion)
- Error scenarios (API failures, invalid data, timeouts)
- De-duplication across runs

**Tools:**
- pytest: Test framework
- Click Testing: CLI invocation
- Docker Compose: Local Notion mock (if needed)
- pytest-timeout: Enforce execution time limits

**Files to Create:**
```
tests/e2e/
└── test_full_pipeline_test_mode.py (6 tests)
```

## Test File Specifications

### Unit Tests

#### tests/unit/test_apify_client.py

**Test Stubs (7 tests):**
1. `test_run_google_maps_scraper_success()` - AC-FEAT-001-001
   - Mock successful Apify actor run
   - Verify correct input parameters sent
   - Assert returns run_id

2. `test_run_google_maps_scraper_retry_on_failure()` - AC-FEAT-001-012
   - Mock 500 error on first 2 attempts, success on 3rd
   - Verify retry logic with exponential backoff
   - Assert successful result after retries

3. `test_wait_for_results_success()` - AC-FEAT-001-001
   - Mock actor status polling (RUNNING → SUCCEEDED)
   - Verify polls until completion
   - Assert returns dataset_id

4. `test_wait_for_results_timeout()` - AC-FEAT-001-013
   - Mock actor status stuck in RUNNING for >600s
   - Verify raises TimeoutError with run_id
   - Assert error message contains run ID

5. `test_parse_results_valid_data()` - AC-FEAT-001-001
   - Mock Apify dataset with 10 valid practices
   - Verify parses to ApifyGoogleMapsResult Pydantic models
   - Assert all required fields present

6. `test_parse_results_invalid_data()` - AC-FEAT-001-016
   - Mock Apify dataset with 1 invalid practice (missing Place ID)
   - Verify raises ValidationError
   - Assert logs invalid record details

7. `test_apify_client_missing_api_key()` - AC-FEAT-001-018
   - Mock missing APIFY_API_KEY environment variable
   - Verify raises ConfigurationError
   - Assert error message contains variable name

#### tests/unit/test_data_filter.py

**Test Stubs (6 tests):**
1. `test_filter_has_website_excludes_missing()` - AC-FEAT-001-002
   - Given practices with and without websites
   - Assert excludes practices without website field
   - Assert includes practices with valid website

2. `test_filter_has_website_excludes_empty()` - AC-FEAT-001-002
   - Given practices with empty string website ("")
   - Assert excludes empty website practices
   - Assert only includes non-empty websites

3. `test_filter_min_reviews_excludes_below_threshold()` - AC-FEAT-001-003
   - Given practices with 5, 10, 15 reviews
   - When filter with min_reviews=10
   - Assert excludes <10, includes >=10

4. `test_filter_min_reviews_default_threshold()` - AC-FEAT-001-003
   - Given practices with various review counts
   - When filter without specifying threshold
   - Assert uses default threshold of 10

5. `test_filter_is_open_excludes_closed()` - AC-FEAT-001-004
   - Given practices with status "OPEN", "CLOSED", "TEMPORARILY_CLOSED"
   - Assert excludes "CLOSED" status only
   - Assert includes "OPEN" and "TEMPORARILY_CLOSED"

6. `test_apply_all_filters_integration()` - AC-FEAT-001-002, AC-FEAT-001-003, AC-FEAT-001-004
   - Given 20 practices (mixed valid/invalid)
   - When apply all filters
   - Assert only practices passing all filters remain

#### tests/unit/test_initial_scorer.py

**Test Stubs (5 tests):**
1. `test_calculate_score_max_score()` - AC-FEAT-001-005
   - Given practice with 100+ reviews, 5.0 rating, website
   - When calculate_score()
   - Assert returns 25 points (max)

2. `test_calculate_score_min_score()` - AC-FEAT-001-005
   - Given practice with 10 reviews, 3.0 rating, website
   - When calculate_score()
   - Assert returns score in 0-25 range

3. `test_calculate_score_review_weight()` - AC-FEAT-001-005
   - Given practices with 10, 50, 100 reviews (same rating)
   - When calculate_score()
   - Assert higher reviews = higher score (logarithmic)

4. `test_calculate_score_rating_weight()` - AC-FEAT-001-005
   - Given practices with same reviews, different ratings (3.0, 4.0, 5.0)
   - When calculate_score()
   - Assert higher rating = higher score (linear)

5. `test_score_batch()` - AC-FEAT-001-005
   - Given list of 10 practices
   - When score_batch()
   - Assert all practices have initial_score field added

#### tests/unit/test_notion_mapper.py

**Test Stubs (5 tests):**
1. `test_map_to_notion_properties_all_fields()` - AC-FEAT-001-010
   - Given practice with all required fields
   - When map_to_notion_properties()
   - Assert Notion properties dict has correct structure

2. `test_map_to_notion_properties_field_types()` - AC-FEAT-001-010
   - Given practice with various data types
   - When map_to_notion_properties()
   - Assert Place ID is Title, Business Name is Rich Text, Phone is Phone Number, etc.

3. `test_create_page_payload_structure()` - AC-FEAT-001-010
   - Given practice
   - When create_page_payload()
   - Assert payload has parent, properties, and children keys

4. `test_create_page_payload_database_id()` - AC-FEAT-001-025
   - Given practice and database_id
   - When create_page_payload()
   - Assert parent.database_id matches expected value

5. `test_map_status_field_default()` - AC-FEAT-001-010
   - Given practice
   - When map_to_notion_properties()
   - Assert Status field is "New Lead"

#### tests/unit/test_notion_batch.py

**Test Stubs (8 tests):**
1. `test_deduplicate_by_place_id()` - AC-FEAT-001-008
   - Given 10 practices with 3 duplicate Place IDs
   - When deduplicate_by_place_id()
   - Assert returns 7 unique practices

2. `test_deduplicate_preserves_first_occurrence()` - AC-FEAT-001-008
   - Given duplicates with different data
   - When deduplicate_by_place_id()
   - Assert keeps first occurrence

3. `test_check_existing_place_ids()` - AC-FEAT-001-009
   - Mock Notion query returning 5 existing Place IDs
   - When check_existing_place_ids()
   - Assert returns set of 5 Place IDs

4. `test_upsert_batch_creates_pages()` - AC-FEAT-001-006
   - Mock Notion create_page API
   - Given 10 practices
   - When upsert_batch(batch_size=10)
   - Assert 10 pages created

5. `test_upsert_batch_rate_limiting()` - AC-FEAT-001-026
   - Mock time.sleep and Notion API
   - Given 30 practices with batch_size=10
   - When upsert_batch()
   - Assert 3 batches created with 3.5s sleep between each

6. `test_upsert_batch_skips_existing()` - AC-FEAT-001-009
   - Mock existing Place IDs in Notion
   - Given 10 practices (5 existing, 5 new)
   - When upsert_batch()
   - Assert only 5 new pages created

7. `test_upsert_batch_retry_on_429()` - AC-FEAT-001-014
   - Mock Notion API returning 429 on first 2 attempts
   - When upsert_batch()
   - Assert retries with backoff, succeeds on 3rd attempt

8. `test_upsert_batch_partial_failure()` - AC-FEAT-001-017
   - Mock Notion API: 8 succeed, 2 fail with 400 error
   - Given 10 practices
   - When upsert_batch()
   - Assert 8 pages created, 2 errors logged

### Integration Tests

#### tests/integration/test_scraping_pipeline.py

**Test Stubs (5 tests):**
1. `test_apify_to_filter_pipeline()` - AC-FEAT-001-001, AC-FEAT-001-002
   - Mock Apify returning 20 practices (10 without websites)
   - Run ApifyClient → DataFilter
   - Assert 10 practices remain after filtering

2. `test_filter_to_score_pipeline()` - AC-FEAT-001-003, AC-FEAT-001-005
   - Given 15 filtered practices
   - Run DataFilter → InitialScorer
   - Assert all practices have initial_score field

3. `test_score_to_notion_pipeline()` - AC-FEAT-001-005, AC-FEAT-001-010
   - Given 10 scored practices
   - Run InitialScorer → NotionMapper
   - Assert all Notion payloads have correct structure

4. `test_full_data_transformation()` - AC-FEAT-001-001, AC-FEAT-001-010
   - Given raw Apify JSON
   - Run full pipeline: ApifyClient.parse → DataFilter → InitialScorer → NotionMapper
   - Assert final Notion payload matches expected schema

5. `test_empty_results_handling()` - AC-FEAT-001-011
   - Mock Apify returning 0 results
   - Run full pipeline
   - Assert logs "No results found", exits gracefully

#### tests/integration/test_notion_integration.py

**Test Stubs (6 tests):**
1. `test_batch_upsert_with_mocked_api()` - AC-FEAT-001-006
   - Mock Notion SDK with VCR.py
   - Given 20 practices
   - Assert batch operations respect rate limits

2. `test_deduplication_across_runs()` - AC-FEAT-001-009
   - Mock Notion database with existing records
   - Run upsert_batch twice with same Place IDs
   - Assert no duplicates created

3. `test_notion_schema_validation()` - AC-FEAT-001-025
   - Mock Notion database schema query
   - Validate required properties exist
   - Assert schema matches expected structure

4. `test_batch_rate_limit_timing()` - AC-FEAT-001-026
   - Mock Notion API and time.sleep
   - Given 50 practices
   - Assert 5 batches with 3.5s delays (measure actual timing)

5. `test_notion_api_retry_logic()` - AC-FEAT-001-014, AC-FEAT-001-015
   - Mock Notion API with intermittent 429 and 500 errors
   - Run upsert_batch
   - Assert retries succeed after transient failures

6. `test_notion_payload_field_mapping()` - AC-FEAT-001-010
   - Given practice with all fields
   - Create Notion page via mocked API
   - Assert all fields mapped correctly in API request

#### tests/integration/test_retry_logic.py

**Test Stubs (4 tests):**
1. `test_apify_retry_exponential_backoff()` - AC-FEAT-001-012
   - Mock Apify API with 500 errors
   - Trigger retry logic
   - Assert backoff timing: 2s, 4s, 8s

2. `test_apify_max_retries_exceeded()` - AC-FEAT-001-012
   - Mock Apify API always returning 500
   - Trigger retry logic (3 attempts)
   - Assert raises exception after max retries

3. `test_notion_retry_on_rate_limit()` - AC-FEAT-001-014
   - Mock Notion API returning 429 with Retry-After header
   - Trigger retry logic
   - Assert respects Retry-After timing

4. `test_notion_retry_success_after_transient_error()` - AC-FEAT-001-015
   - Mock Notion API: 500 → 500 → 200
   - Trigger retry logic
   - Assert succeeds after 2 retries

### End-to-End Tests

#### tests/e2e/test_full_pipeline_test_mode.py

**Test Stubs (6 tests):**
1. `test_cli_test_mode_flag()` - AC-FEAT-001-007
   - Invoke CLI with --test flag
   - Mock Apify to return 10 practices
   - Assert pipeline processes exactly 10 practices

2. `test_cli_test_mode_full_pipeline()` - AC-FEAT-001-007
   - Invoke CLI with --test
   - Mock Apify and Notion APIs
   - Assert all stages complete: scrape → filter → score → upload

3. `test_cli_production_mode()` - AC-FEAT-001-001
   - Invoke CLI without --test flag
   - Mock Apify to return 150 practices
   - Assert pipeline processes 150 practices

4. `test_cli_missing_env_vars()` - AC-FEAT-001-018
   - Unset APIFY_API_KEY environment variable
   - Invoke CLI
   - Assert exits with ConfigurationError

5. `test_cli_performance_benchmark()` - AC-FEAT-001-019
   - Invoke CLI with --test (10 practices)
   - Measure execution time
   - Assert completes within expected time (<60s for test mode)

6. `test_cli_error_handling()` - AC-FEAT-001-012, AC-FEAT-001-014
   - Mock API failures (Apify 500, Notion 429)
   - Invoke CLI
   - Assert retry logic activates, pipeline recovers

## Test Data & Fixtures

### Fixtures Location
```
tests/fixtures/
├── apify_responses/
│   ├── google_maps_10_practices.json
│   ├── google_maps_150_practices.json
│   └── google_maps_empty_results.json
├── filtered_practices/
│   ├── valid_practices_10.json
│   └── invalid_practices_mixed.json
└── notion_schemas/
    └── database_schema.json
```

### Fixture Content
- **apify_responses**: Mock JSON responses from Apify actor (Place ID, name, address, phone, website, reviews, rating)
- **filtered_practices**: Pre-filtered practices for testing scoring and Notion upload
- **notion_schemas**: Notion database schema for validation tests

## Mocking Strategy

### Apify API Mocking
```python
# Mock successful scraper run
@patch('apify_client.ApifyClient')
def test_apify_success(mock_client):
    mock_client.return_value.actor('compass/crawler-google-places').call.return_value = {
        'id': 'run_123',
        'status': 'SUCCEEDED',
        'defaultDatasetId': 'dataset_456'
    }
    # Test code here
```

### Notion API Mocking
```python
# Mock Notion page creation with rate limiting
@patch('notion_client.Client')
@patch('time.sleep')  # Mock sleep to speed up tests
def test_notion_batch(mock_sleep, mock_client):
    mock_client.return_value.pages.create.return_value = {'id': 'page_123'}
    # Test code here
```

### VCR.py for Integration Tests
```python
# Record real API interactions once, replay in tests
@vcr.use_cassette('fixtures/vcr_cassettes/notion_batch_upsert.yaml')
def test_notion_integration():
    # Makes real API call first time, replays from cassette after
    pass
```

## Coverage Goals

### Component-Level Coverage
- ApifyClient: 90%+ (critical for data source)
- DataFilter: 95%+ (business logic)
- InitialScorer: 90%+ (scoring algorithm)
- NotionMapper: 85%+ (transformation logic)
- NotionBatchUpserter: 95%+ (critical for data persistence)

### Overall Coverage
- Target: 80%+ overall coverage
- Critical paths: 95%+ (scraping, filtering, scoring, uploading)
- Error handling: 100% (all retry/fallback logic)

## Test Execution

### Running Tests
```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/

# With coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Specific test file
pytest tests/unit/test_apify_client.py -v

# Specific test function
pytest tests/unit/test_apify_client.py::test_run_google_maps_scraper_success -v
```

### CI/CD Integration
```bash
# Run in CI pipeline
pytest tests/ --cov=src --cov-report=xml --cov-fail-under=80
```

## Manual Testing Requirements

See `manual-test.md` for human-driven testing scenarios:
- Visual verification of Notion records
- Cost validation (Apify billing)
- Performance benchmarking (150 practices)
- Error recovery validation (API failures)

## Test Environment Setup

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock pytest-timeout vcrpy freezegun

# Set test environment variables
export APIFY_API_KEY="test_key_123"
export NOTION_API_KEY="test_key_456"
export NOTION_DATABASE_ID="test_db_789"
```

### Mock Services
- Use pytest fixtures for consistent test data
- Mock external APIs to avoid costs and ensure test speed
- Use VCR.py for integration tests (record real API once, replay)

## Success Criteria

- [ ] All 31 test stubs created across 9 test files
- [ ] Test fixtures created with realistic data
- [ ] Mocking strategy validated (no real API calls in unit/integration tests)
- [ ] Coverage goals met (80%+ overall, 95%+ critical paths)
- [ ] All tests pass in CI/CD pipeline
- [ ] Test execution time <5 minutes for full suite
- [ ] Manual testing scenarios validated per manual-test.md

---

**Total Test Files:** 9
**Total Test Stubs:** 31
**Template Version:** 1.0.0
**Last Updated:** 2025-11-03
