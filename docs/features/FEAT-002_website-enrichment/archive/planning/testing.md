# Testing Strategy: Website Enrichment & LLM Extraction

**Feature ID:** FEAT-002
**Created:** 2025-11-03
**Test Coverage Goal:** 80%+

## Test Strategy Overview

FEAT-002 testing focuses on verifying multi-page website scraping, OpenAI structured output extraction, cost tracking with tiktoken, Notion partial updates, re-enrichment logic, and automatic scoring trigger. Testing follows TDD principles: write test stubs during planning (Phase 1), make them functional during implementation (Phase 2), validate against acceptance criteria. Priority: core logic (WebsiteScraper, LLMExtractor, CostTracker, EnrichmentOrchestrator) at 80%+ coverage, integration tests for external APIs (Crawl4AI, OpenAI, Notion), manual testing for end-to-end validation.

**Testing Levels:**
- ✅ Unit Tests: Core classes (WebsiteScraper, LLMExtractor, CostTracker, EnrichmentOrchestrator, NotionClient extensions)
- ✅ Integration Tests: Crawl4AI deep crawling, OpenAI structured outputs, Notion updates, end-to-end pipeline
- ✅ E2E Tests: Not applicable (backend-only feature, no user interface)
- ✅ Manual Tests: Test mode execution (10 practices), cost tracking verification, Notion field inspection

## Unit Tests

### Test Files to Create

#### `tests/unit/test_website_scraper.py`

**Purpose:** Test WebsiteScraper with Crawl4AI BFSDeepCrawlStrategy for multi-page scraping

**Test Stubs:**
1. **Test: test_bfs_deep_crawl_strategy_configuration (AC-FEAT-002-001)**
   - **Given:** WebsiteScraper initialized with BFSDeepCrawlStrategy config
   - **When:** Strategy is created
   - **Then:** max_depth=1, max_pages=5, include_external=False, URL pattern filter = *about*, *team*, *staff*, *contact*
   - **Mocks:** None (configuration test)

2. **Test: test_scrape_multi_page_success (AC-FEAT-002-001)**
   - **Given:** Practice website with homepage + /about + /team pages
   - **When:** scrape_multi_page() is called
   - **Then:** Returns List[WebsiteData] with 3 pages, all success=True, cleaned_text populated
   - **Mocks:** AsyncWebCrawler (mock successful CrawlResult objects)

3. **Test: test_scrape_multi_page_partial_failure (AC-FEAT-002-101)**
   - **Given:** Practice website where /team page times out
   - **When:** scrape_multi_page() is called
   - **Then:** Returns homepage (success=True) and /about (success=True), /team (success=False, error_message="timeout")
   - **Mocks:** AsyncWebCrawler (mock timeout for /team page)

4. **Test: test_scrape_multi_page_total_failure (AC-FEAT-002-102)**
   - **Given:** Practice website with DNS error (all pages fail)
   - **When:** scrape_multi_page() is called
   - **Then:** Raises WebsiteConnectionError with practice name and error details
   - **Mocks:** AsyncWebCrawler (mock connection refused)

5. **Test: test_url_pattern_filter (AC-FEAT-002-001)**
   - **Given:** Website with pages: /, /about, /team, /blog, /contact, /services
   - **When:** BFSDeepCrawlStrategy filters URLs
   - **Then:** Only /, /about, /team, /contact are crawled (blog and services excluded)
   - **Mocks:** URLPatternFilter (verify pattern matching)

6. **Test: test_concurrent_scraping_not_blocking (AC-FEAT-002-002)**
   - **Given:** 5 practice URLs to scrape concurrently
   - **When:** scrape_batch() processes them
   - **Then:** All 5 complete within 20 seconds (not 5×15s=75s if sequential)
   - **Mocks:** AsyncWebCrawler (mock delays for each practice)

7. **Test: test_cache_enabled (AC-FEAT-002-005 from user decisions)**
   - **Given:** WebsiteScraper with cache_mode=CacheMode.ENABLED
   - **When:** Same URL scraped twice
   - **Then:** Second scrape returns cached result (no network call)
   - **Mocks:** AsyncWebCrawler (verify cache hit)

---

#### `tests/unit/test_llm_extractor.py`

**Purpose:** Test LLMExtractor with OpenAI structured outputs and cost tracking

**Test Stubs:**
1. **Test: test_extract_practice_data_structured_output (AC-FEAT-002-003)**
   - **Given:** Scraped website pages with cleaned text (homepage + /about + /team)
   - **When:** extract_practice_data() calls OpenAI with beta.chat.completions.parse
   - **Then:** Returns VetPracticeExtraction Pydantic object with all fields populated or null
   - **Mocks:** OpenAI client (mock successful response.choices[0].message.parsed)

2. **Test: test_vet_count_extraction_high_confidence (AC-FEAT-002-004)**
   - **Given:** Website text: "Our team: Dr. Jane Smith, Dr. John Doe, Dr. Mary Johnson"
   - **When:** extract_practice_data() is called
   - **Then:** vet_count_total=3, vet_count_confidence="high"
   - **Mocks:** OpenAI client (mock extraction result)

3. **Test: test_vet_count_extraction_low_confidence (AC-FEAT-002-104)**
   - **Given:** Website text: "Our team of veterinarians" (vague mention)
   - **When:** extract_practice_data() is called
   - **Then:** vet_count_total=null, vet_count_confidence="low"
   - **Mocks:** OpenAI client (mock low confidence result)

4. **Test: test_decision_maker_extraction_explicit_email (AC-FEAT-002-005)**
   - **Given:** Website text: "Contact Dr. Smith (Owner) at drsmith@example.com"
   - **When:** extract_practice_data() is called
   - **Then:** decision_maker.name="Dr. Smith", decision_maker.role="Owner", decision_maker.email="drsmith@example.com"
   - **Mocks:** OpenAI client (mock decision maker extraction)

5. **Test: test_decision_maker_no_email_found (AC-FEAT-002-109)**
   - **Given:** Website text: "Dr. Jane Smith (Owner)" (no email address)
   - **When:** extract_practice_data() is called
   - **Then:** decision_maker.name="Dr. Jane Smith", decision_maker.role="Owner", decision_maker.email=null
   - **Mocks:** OpenAI client (mock no email result)

6. **Test: test_service_detection_emergency_24_7 (AC-FEAT-002-006)**
   - **Given:** Website text: "We offer 24/7 emergency services"
   - **When:** extract_practice_data() is called
   - **Then:** emergency_24_7=True
   - **Mocks:** OpenAI client (mock service detection)

7. **Test: test_technology_indicators_detection (AC-FEAT-002-007)**
   - **Given:** Website text: "Book appointments online" and "Patient portal login"
   - **When:** extract_practice_data() is called
   - **Then:** online_booking=True, patient_portal=True
   - **Mocks:** OpenAI client (mock technology detection)

8. **Test: test_personalization_context_extraction (AC-FEAT-002-008)**
   - **Given:** Website text: "Opened 2nd location in Newton Oct 2024" and "AAHA accredited"
   - **When:** extract_practice_data() is called
   - **Then:** personalization_context=["Opened 2nd location in Newton Oct 2024"], awards_accreditations=["AAHA accredited"]
   - **Mocks:** OpenAI client (mock context extraction)

9. **Test: test_personalization_context_empty (AC-FEAT-002-105)**
   - **Given:** Website with only basic contact info (no awards, history, specialties)
   - **When:** extract_practice_data() is called
   - **Then:** personalization_context=[] (empty array)
   - **Mocks:** OpenAI client (mock empty context)

10. **Test: test_openai_rate_limit_retry (AC-FEAT-002-103)**
    - **Given:** OpenAI API returns 429 rate limit on first attempt
    - **When:** extract_practice_data() is called
    - **Then:** Retries with exponential backoff (1s, 2s, 4s), succeeds on 2nd attempt
    - **Mocks:** OpenAI client (mock 429 then success)

11. **Test: test_token_truncation (AC from PRD)**
    - **Given:** Website pages concatenated to 12000 characters
    - **When:** extract_practice_data() prepares input
    - **Then:** Text truncated to 8000 characters (~2000 tokens) before API call
    - **Mocks:** None (truncation logic test)

---

#### `tests/unit/test_cost_tracker.py`

**Purpose:** Test CostTracker with tiktoken token counting and budget monitoring

**Test Stubs:**
1. **Test: test_tiktoken_token_counting (AC-FEAT-002-009)**
   - **Given:** Sample text with known token count (verified with tiktoken CLI)
   - **When:** count_tokens() is called
   - **Then:** Returns correct token count using o200k_base encoding for gpt-4o-mini
   - **Mocks:** None (tiktoken library test)

2. **Test: test_cost_estimation (AC-FEAT-002-009)**
   - **Given:** 2000 input tokens + 500 output tokens
   - **When:** estimate_cost() is called
   - **Then:** Returns $0.0006 ((2000 × $0.15/1M) + (500 × $0.60/1M))
   - **Mocks:** None (cost calculation test)

3. **Test: test_check_budget_under_threshold (AC-FEAT-002-009)**
   - **Given:** cumulative_cost=$0.50, estimated_cost=$0.10, max_budget=$1.00
   - **When:** check_budget(estimated_cost=$0.10) is called
   - **Then:** Returns True (under threshold, can proceed)
   - **Mocks:** None (budget check test)

4. **Test: test_check_budget_exceeds_threshold (AC-FEAT-002-010)**
   - **Given:** cumulative_cost=$0.95, estimated_cost=$0.08, max_budget=$1.00
   - **When:** check_budget(estimated_cost=$0.08) is called
   - **Then:** Raises CostLimitExceeded with message "Cost limit exceeded: $0.95 + $0.08 > $1.00"
   - **Mocks:** None (threshold abort test)

5. **Test: test_track_call_updates_cumulative_cost (AC-FEAT-002-009)**
   - **Given:** Initial cumulative_cost=$0.00
   - **When:** track_call(input_tokens=2000, output_tokens=500) is called
   - **Then:** cumulative_cost updated to $0.0006, call_count=1
   - **Mocks:** None (tracking test)

6. **Test: test_cost_logging_every_10_practices (AC-FEAT-002-209)**
   - **Given:** CostTracker with log_interval=10
   - **When:** 15 API calls tracked
   - **Then:** Cost logged at calls #10, final summary at end
   - **Mocks:** Logger (verify log entries)

---

#### `tests/unit/test_enrichment_orchestrator.py`

**Purpose:** Test EnrichmentOrchestrator coordination of scraping, extraction, updates, retry, and scoring trigger

**Test Stubs:**
1. **Test: test_enrich_all_practices_success (AC-FEAT-002-002, AC-FEAT-002-012)**
   - **Given:** 10 practices needing enrichment (test mode)
   - **When:** enrich_all_practices(test_mode=True) is called
   - **Then:** All 10 practices scraped, extracted, updated in Notion, enrichment_status="Completed"
   - **Mocks:** WebsiteScraper, LLMExtractor, NotionClient (all successful)

2. **Test: test_concurrent_scraping_batches (AC-FEAT-002-002)**
   - **Given:** 150 practices, max_concurrent=5
   - **When:** enrich_all_practices() processes them
   - **Then:** Practices processed in batches of 5 (30 batches total)
   - **Mocks:** WebsiteScraper (track batch calls)

3. **Test: test_re_enrichment_filter_30_days (AC-FEAT-002-013)**
   - **Given:** Notion query returns 100 stale practices (>30 days old) + 50 never enriched
   - **When:** enrich_all_practices() queries Notion
   - **Then:** 150 practices returned (recently enriched <30 days excluded)
   - **Mocks:** NotionClient (mock query filter)

4. **Test: test_cost_abort_mid_batch (AC-FEAT-002-110)**
   - **Given:** Cumulative cost reaches $1.01 after 120 extractions
   - **When:** enrich_all_practices() continues processing
   - **Then:** CostLimitExceeded raised, pipeline aborts, 120 practices enriched (no rollback)
   - **Mocks:** CostTracker (mock threshold breach at #121)

5. **Test: test_retry_failed_scrapes (AC-FEAT-002-106)**
   - **Given:** 8 practices fail initial scrape (timeouts, connection errors)
   - **When:** Retry logic executes at end of batch
   - **Then:** All 8 practices re-scraped once, successful retries processed normally
   - **Mocks:** WebsiteScraper (mock initial failures, then successes)

6. **Test: test_persistent_failure_logging (AC-FEAT-002-107)**
   - **Given:** Practice fails both initial scrape and retry (DNS error)
   - **When:** Retry completes with failure
   - **Then:** NotionClient updates practice with enrichment_status="Failed", enrichment_error="DNS resolution failed"
   - **Mocks:** WebsiteScraper (mock persistent failure), NotionClient (verify error logging)

7. **Test: test_auto_trigger_scoring_enabled (AC-FEAT-002-015)**
   - **Given:** auto_trigger_scoring=True, scoring_service provided
   - **When:** Practice successfully enriched
   - **Then:** ScoringService.calculate_icp_score() called with practice_id and enrichment_data
   - **Mocks:** ScoringService (verify call), NotionClient (verify score update)

8. **Test: test_auto_trigger_scoring_disabled (AC-FEAT-002-016)**
   - **Given:** auto_trigger_scoring=False
   - **When:** Practice successfully enriched
   - **Then:** No scoring calls made, enrichment completes successfully
   - **Mocks:** ScoringService (verify no calls)

9. **Test: test_scoring_failure_graceful_degradation (AC-FEAT-002-108)**
   - **Given:** auto_trigger_scoring=True, ScoringService raises ScoringError
   - **When:** Practice enriched and scoring attempted
   - **Then:** Error logged, enrichment_status="Completed", next practice processed normally
   - **Mocks:** ScoringService (mock error), Logger (verify error logged)

10. **Test: test_test_mode_limits_to_10_practices (AC-FEAT-002-014)**
    - **Given:** enrich_all_practices(test_mode=True)
    - **When:** Notion query executed
    - **Then:** Notion query includes limit=10, exactly 10 practices enriched
    - **Mocks:** NotionClient (verify limit=10 in query)

---

#### `tests/unit/test_notion_client_enrichment.py`

**Purpose:** Test NotionClient.update_practice_enrichment() for partial updates with field preservation

**Test Stubs:**
1. **Test: test_update_practice_enrichment_field_mapping (AC-FEAT-002-402)**
   - **Given:** VetPracticeExtraction with all fields populated
   - **When:** update_practice_enrichment() is called
   - **Then:** Notion payload contains all enrichment fields mapped correctly (vet count, decision maker, services, etc.)
   - **Mocks:** Notion client (verify payload structure)

2. **Test: test_partial_update_preserves_sales_fields (AC-FEAT-002-011)**
   - **Given:** Existing Notion record with Status="Qualified", Assigned To="John", Call Notes="Follow up"
   - **When:** update_practice_enrichment() updates only enrichment fields
   - **Then:** Payload does NOT include Status, Assigned To, Call Notes (auto-preserved by Notion API)
   - **Mocks:** Notion client (verify excluded fields)

3. **Test: test_enrichment_status_and_date_updated (AC-FEAT-002-012)**
   - **Given:** Successful enrichment with extraction_timestamp
   - **When:** update_practice_enrichment() is called
   - **Then:** enrichment_status="Completed", last_enrichment_date=extraction_timestamp
   - **Mocks:** Notion client (verify status and date fields)

4. **Test: test_null_values_handled_gracefully (AC-FEAT-002-401)**
   - **Given:** VetPracticeExtraction with decision_maker.email=null
   - **When:** update_practice_enrichment() maps to Notion
   - **Then:** Decision Maker Email field omitted from payload (Notion accepts null as empty)
   - **Mocks:** Notion client (verify null handling)

5. **Test: test_re_enrichment_query_filter (AC-FEAT-002-013)**
   - **Given:** Notion database with mixed enrichment statuses and dates
   - **When:** query_practices_for_enrichment() is called
   - **Then:** Filter uses OR condition: enrichment_status != "Completed" OR last_enriched_date > 30 days ago
   - **Mocks:** Notion client (verify filter structure)

---

### Unit Test Coverage Goals

- **Functions:** All public functions tested (scrape_multi_page, extract_practice_data, check_budget, enrich_all_practices, update_practice_enrichment)
- **Branches:** All conditional branches covered (retry logic, cost abort, scoring trigger, test mode)
- **Edge Cases:** Boundary conditions tested (empty context, null email, low confidence, cost threshold, partial failures)
- **Error Handling:** All error paths tested (timeouts, rate limits, connection errors, cost overruns, scoring failures)

**Target Coverage:** 80% line coverage

## Integration Tests

### Test Files to Create

#### `tests/integration/test_crawl4ai_deep_crawling.py`

**Purpose:** Test Crawl4AI BFSDeepCrawlStrategy integration with real websites

**Test Stubs:**
1. **Test: test_bfs_deep_crawl_real_website (AC-FEAT-002-301)**
   - **Components:** WebsiteScraper, Crawl4AI AsyncWebCrawler
   - **Setup:** 3 real vet websites with known structures (homepage + /about + /team)
   - **Scenario:** Scrape each website with BFSDeepCrawlStrategy, verify 2-4 pages returned per site
   - **Assertions:** All pages have success=True, cleaned_text populated, URL pattern filter works

2. **Test: test_concurrent_deep_crawl (AC-FEAT-002-002)**
   - **Components:** WebsiteScraper, Crawl4AI AsyncWebCrawler
   - **Setup:** 5 real vet websites
   - **Scenario:** Scrape all 5 concurrently (max_concurrent=5), measure total time
   - **Assertions:** Total time <25 seconds (not 5×15s=75s sequential), all 5 complete successfully

3. **Test: test_url_pattern_filter_integration (AC-FEAT-002-001)**
   - **Components:** WebsiteScraper, URLPatternFilter
   - **Setup:** Website with /about, /team, /blog, /services, /contact
   - **Scenario:** Crawl with URL pattern filter (*about*, *team*, *contact*)
   - **Assertions:** Only /about, /team, /contact crawled (blog and services excluded)

---

#### `tests/integration/test_openai_structured_outputs.py`

**Purpose:** Test OpenAI beta.chat.completions.parse integration with real API

**Test Stubs:**
1. **Test: test_structured_output_extraction_real_api (AC-FEAT-002-302)**
   - **Components:** LLMExtractor, OpenAI client
   - **Setup:** 5 sample website texts (from real vet websites)
   - **Scenario:** Extract data using beta.chat.completions.parse with VetPracticeExtraction model
   - **Assertions:** All responses valid Pydantic objects (no parsing errors), 100% schema compliance

2. **Test: test_token_counting_accuracy (AC-FEAT-002-303)**
   - **Components:** LLMExtractor, tiktoken, OpenAI client
   - **Setup:** 10 sample website texts with varying lengths
   - **Scenario:** Count tokens with tiktoken, call OpenAI, compare to actual API usage
   - **Assertions:** tiktoken estimates within 5% of actual API usage (response.usage.prompt_tokens)

3. **Test: test_cost_tracking_real_api (AC-FEAT-002-202)**
   - **Components:** LLMExtractor, CostTracker, OpenAI client
   - **Setup:** 10 sample extractions
   - **Scenario:** Track cost with CostTracker, verify against actual OpenAI charges
   - **Assertions:** Total cost ≤$0.006 for 10 extractions (avg $0.0006 per extraction)

---

#### `tests/integration/test_notion_partial_updates.py`

**Purpose:** Test Notion API partial update integration with real database

**Test Stubs:**
1. **Test: test_partial_update_field_preservation (AC-FEAT-002-304)**
   - **Components:** NotionClient, Notion API
   - **Setup:** Create 3 test Notion records with sales fields (Status, Assigned To, Call Notes)
   - **Scenario:** Update with update_practice_enrichment() (only enrichment fields)
   - **Assertions:** Sales fields unchanged after update, enrichment fields updated correctly

2. **Test: test_re_enrichment_query (AC-FEAT-002-013)**
   - **Components:** NotionClient, Notion API
   - **Setup:** Create 10 test records: 3 new, 4 enriched <30 days, 3 enriched >30 days
   - **Scenario:** Query with query_practices_for_enrichment()
   - **Assertions:** Returns 6 practices (3 new + 3 stale), excludes 4 recently enriched

3. **Test: test_enrichment_status_update (AC-FEAT-002-012)**
   - **Components:** NotionClient, Notion API
   - **Setup:** Create 1 test record with enrichment_status=null
   - **Scenario:** Update with update_practice_enrichment()
   - **Assertions:** enrichment_status="Completed", last_enrichment_date set to current timestamp

---

#### `tests/integration/test_enrichment_pipeline.py`

**Purpose:** End-to-end integration test of full enrichment pipeline

**Test Stubs:**
1. **Test: test_enrichment_pipeline_end_to_end (AC-FEAT-002-014)**
   - **Components:** EnrichmentOrchestrator, WebsiteScraper, LLMExtractor, NotionClient, CostTracker
   - **Setup:** 10 real vet websites, test Notion database, OpenAI API key
   - **Scenario:** Run enrich_all_practices(test_mode=True) end-to-end
   - **Assertions:** All 10 practices enriched, Notion updated, cost ≤$0.06 (10 × $0.0006), execution time ≤2 minutes

2. **Test: test_retry_logic_integration (AC-FEAT-002-106)**
   - **Components:** EnrichmentOrchestrator, WebsiteScraper
   - **Setup:** 5 websites, 2 with intermittent failures (mock timeout on first attempt)
   - **Scenario:** Run pipeline, verify retry logic
   - **Assertions:** 2 failed practices retried once, both succeed on retry, 5 total enriched

3. **Test: test_scoring_trigger_integration (AC-FEAT-002-015)**
   - **Components:** EnrichmentOrchestrator, ScoringService (mock), NotionClient
   - **Setup:** 3 practices, auto_trigger_scoring=True, mock ScoringService
   - **Scenario:** Run pipeline, verify scoring triggered for each
   - **Assertions:** ScoringService.calculate_icp_score() called 3 times, Notion updated with scores

---

### Integration Test Scope

**Internal Integrations:**
- WebsiteScraper → Crawl4AI AsyncWebCrawler: Multi-page scraping with BFSDeepCrawlStrategy
- LLMExtractor → OpenAI client: Structured output extraction with beta.chat.completions.parse
- CostTracker → tiktoken → OpenAI: Token counting and cost tracking
- EnrichmentOrchestrator → WebsiteScraper + LLMExtractor + NotionClient: Full pipeline coordination

**External Integrations:**
- Crawl4AI (real websites): Test with 3-5 known vet websites (varying structures)
- OpenAI API (real API): Test with test mode (10 practices) to validate structured outputs
- Notion API (test database): Create dedicated test database for integration tests

**Mock Strategy:**
- **Fully Mocked:** FEAT-003 ScoringService (not yet implemented), transient failures (timeouts, rate limits)
- **Partially Mocked:** OpenAI (use real API in test mode, mock for unit tests)
- **Real:** Crawl4AI (scrape real websites), Notion (use test database)

## E2E Tests (If Applicable)

Not applicable - FEAT-002 is backend-only feature with no user interface. Integration tests serve as end-to-end validation.

## Manual Testing

### Manual Test Scenarios

*See `manual-test.md` for detailed step-by-step instructions.*

**Quick Reference:**
1. **Test Mode Execution (10 Practices):** Verify pipeline completes within 1-2 minutes, exactly 10 practices enriched
2. **Notion Field Verification:** Inspect 5 enriched Notion records, verify all enrichment fields populated correctly
3. **Cost Tracking Validation:** Review logs, verify cost logged every 10 practices, total cost ≤$0.50
4. **Sales Field Preservation:** Update existing Notion record with sales fields, verify preserved after enrichment
5. **Re-enrichment Logic:** Manually set last_enrichment_date to >30 days ago, verify practice re-enriched on next run

**Manual Test Focus:**
- **Data Verification:** Inspect Notion records for correct field mappings, null handling, confidence levels
- **Cost Tracking:** Verify cost logs match expected calculations, cumulative cost tracking accurate
- **Error Handling:** Trigger failures (invalid URL, timeout), verify retry logic and error logging
- **Performance:** Measure execution time for 10 practices (test mode), verify ≤2 minutes

## Test Data Requirements

### Fixtures & Seed Data

**Unit Test Fixtures:**
```python
# tests/fixtures/website_sample.html
SAMPLE_WEBSITE_HOMEPAGE = """
<html>
  <body>
    <h1>Boston Veterinary Clinic</h1>
    <p>We offer 24/7 emergency services and online booking.</p>
  </body>
</html>
"""

SAMPLE_WEBSITE_TEAM = """
<html>
  <body>
    <h2>Our Team</h2>
    <ul>
      <li>Dr. Jane Smith, DVM (Owner) - drsmith@bostonvet.com</li>
      <li>Dr. John Doe, DVM</li>
      <li>Dr. Mary Johnson, DVM</li>
    </ul>
  </body>
</html>
"""

# tests/fixtures/extraction_sample.json
{
  "vet_count_total": 3,
  "vet_count_confidence": "high",
  "decision_maker": {
    "name": "Dr. Jane Smith",
    "role": "Owner",
    "email": "drsmith@bostonvet.com",
    "phone": null
  },
  "emergency_24_7": true,
  "online_booking": true,
  "personalization_context": ["Opened 2nd location in Newton Oct 2024"],
  "awards_accreditations": ["AAHA accredited"]
}
```

**Integration Test Data:**
- **Real Websites:** List of 5 known vet websites with stable structures (for Crawl4AI integration tests)
- **Test Notion Database:** Dedicated test database ID for integration tests (separate from production)
- **OpenAI Test API Key:** Use test mode with real API key, limit to 10 practices to minimize cost

**E2E Test Data:**
Not applicable (no E2E tests for backend feature)

## Mocking Strategy

### What to Mock

**Always Mock:**
- OpenAI API in unit tests (to avoid costs, use mock responses)
- FEAT-003 ScoringService (not yet implemented, use mock class)
- Transient failures (timeouts, rate limits) for retry logic testing
- Notion API in unit tests (use mock responses)

**Sometimes Mock:**
- Crawl4AI AsyncWebCrawler (mock in unit tests, real in integration tests)
- OpenAI API in integration tests (use real API in test mode with 10 practices)
- Notion API in integration tests (use real test database)

**Never Mock:**
- Core feature logic being tested (WebsiteScraper, LLMExtractor, CostTracker, EnrichmentOrchestrator)
- tiktoken library (actual token counting needed for accuracy)
- Pydantic validation (actual schema validation needed)

### Mocking Approach

**Framework:** pytest with pytest-mock

**Mock Examples:**
```python
# Mock OpenAI client for unit tests
@pytest.fixture
def mock_openai_client(mocker):
    mock_client = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.choices[0].message.parsed = VetPracticeExtraction(
        vet_count_total=3,
        vet_count_confidence="high",
        # ... other fields
    )
    mock_response.usage.prompt_tokens = 2000
    mock_response.usage.completion_tokens = 500
    mock_client.beta.chat.completions.parse.return_value = mock_response
    return mock_client

# Mock Crawl4AI AsyncWebCrawler for unit tests
@pytest.fixture
def mock_async_web_crawler(mocker):
    mock_crawler = mocker.AsyncMock()
    mock_result = mocker.Mock()
    mock_result.success = True
    mock_result.html = "<html>...</html>"
    mock_result.cleaned_html = "Cleaned text..."
    mock_result.url = "https://example-vet.com"
    mock_crawler.arun.return_value = [mock_result]
    return mock_crawler

# Mock ScoringService for integration tests
@pytest.fixture
def mock_scoring_service(mocker):
    mock_service = mocker.AsyncMock()
    mock_score = mocker.Mock()
    mock_score.total_score = 85
    mock_service.calculate_icp_score.return_value = mock_score
    return mock_service
```

## Test Execution

### Running Tests Locally

**Unit Tests:**
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_website_scraper.py -v

# Run with coverage report
pytest tests/unit/ --cov=src/enrichment --cov-report=html --cov-report=term
```

**Integration Tests:**
```bash
# Run all integration tests
pytest tests/integration/ -v

# Run with real OpenAI API (requires OPENAI_API_KEY env var)
OPENAI_API_KEY=sk-proj-xxx pytest tests/integration/test_openai_structured_outputs.py -v

# Run with real Notion API (requires NOTION_API_KEY and test database)
NOTION_API_KEY=secret_xxx pytest tests/integration/test_notion_partial_updates.py -v
```

**All Tests:**
```bash
# Run all tests (unit + integration)
pytest tests/ -v

# Run with coverage (unit tests only for coverage metrics)
pytest tests/unit/ --cov=src/enrichment --cov-report=html
```

### CI/CD Integration (Phase 2)

**Pipeline Stages:**
1. Unit tests (run on every commit) - fast, no external dependencies
2. Integration tests with mocked external services (run on every commit)
3. Integration tests with real APIs (run on PR, pre-merge) - requires API keys in CI secrets
4. Coverage report generation (fail if <80%)
5. Test result artifacts (JUnit XML, coverage HTML)

**Failure Handling:**
- Failing tests block merge
- Coverage drops below 80% block merge
- Flaky test detection (retry failed tests once)

## Coverage Goals

### Coverage Targets

| Test Level | Target Coverage | Minimum Acceptable |
|------------|----------------|-------------------|
| Unit | 85% | 80% |
| Integration | 70% | 60% |
| E2E | N/A (workflow-based) | N/A |

### Critical Paths

**Must Have 100% Coverage:**
- CostTracker.check_budget() (cost abort logic - critical to prevent runaway costs)
- EnrichmentOrchestrator retry logic (prevents data loss from transient failures)
- NotionClient.update_practice_enrichment() field preservation (prevents overwriting sales data)

**Can Have Lower Coverage:**
- Logging statements (observability, not critical logic)
- Error message formatting (nice-to-have, not functional)
- Mock setup code in test files

## Performance Testing

### Performance Benchmarks

**Requirement:** From AC-FEAT-002-201 (Performance - Total Execution Time)

**Test Approach:**
- **Tool:** pytest-benchmark plugin for Python
- **Scenarios:**
  1. **10 practices (test mode):** ≤2 minutes total execution
  2. **150 practices (production):** ≤14 minutes total execution (scraping ≤12 min, LLM ≤2 min, Notion ≤1 min, retry ≤2 min)
  3. **Single practice scraping:** ≤20 seconds (multi-page)
  4. **Single LLM extraction:** ≤1 second (API call + token counting)

**Acceptance:**
- 10 practices complete within 2 minutes (integration test assertion)
- Single practice scraping ≤20 seconds (benchmark test)
- Cost ≤$0.006 for 10 practices (integration test assertion)

## Security Testing

### Security Test Scenarios

1. **API Key Protection:** Verify OpenAI API key never logged in plaintext (AC-FEAT-002-208)
2. **Environment Variable Loading:** Verify API keys loaded from .env, not hardcoded
3. **Error Messages:** Verify API keys not included in error messages or stack traces
4. **Log File Inspection:** Grep log files for patterns like "sk-proj-" (should be masked)

**Tools:**
- pytest tests with log inspection
- Manual review of log outputs

## Test Stub Generation (Phase 1)

*These test files will be created with TODO stubs during planning:*

```
tests/
├── unit/
│   ├── test_website_scraper.py (7 test stubs)
│   ├── test_llm_extractor.py (11 test stubs)
│   ├── test_cost_tracker.py (6 test stubs)
│   ├── test_enrichment_orchestrator.py (10 test stubs)
│   └── test_notion_client_enrichment.py (5 test stubs)
└── integration/
    ├── test_crawl4ai_deep_crawling.py (3 test stubs)
    ├── test_openai_structured_outputs.py (3 test stubs)
    ├── test_notion_partial_updates.py (3 test stubs)
    └── test_enrichment_pipeline.py (3 test stubs)
```

**Total Test Stubs:** 51 test functions with TODO comments

## Out of Scope

*What we're explicitly NOT testing in this phase:*

- **Image analysis (OCR, logo extraction):** Not in FEAT-002 scope
- **Review sentiment analysis:** Not in FEAT-002 scope
- **Email validation/verification (SMTP checks):** Not in FEAT-002 scope (only explicit email extraction)
- **Deep link analysis beyond /about and /team:** Not in FEAT-002 scope (max_depth=1, max_pages=5)
- **Checkpointing/resume from failure:** Deferred to Phase 2 (pipeline is fast enough to re-run)
- **Asynchronous event bus for FEAT-002 → FEAT-003:** Deferred to Phase 2 (using synchronous trigger for MVP)

---

**Next Steps:**
1. Planner will generate test stub files based on this strategy
2. Phase 2: Implementer will make stubs functional (TDD Red-Green-Refactor)
3. Phase 2: Tester will execute and validate against acceptance criteria
