📘 Test-Driven Development Guide for FEAT-001

  How Test Stubs Work

  The test stubs are your implementation roadmap. Each test file maps directly to a component you need to build. Here's the workflow:

  TDD Workflow (Red → Green → Refactor)

  ┌─────────────────────────────────────────────────────────────┐
  │ PHASE 1: RED (Test Fails)                                   │
  ├─────────────────────────────────────────────────────────────┤
  │ 1. Pick a test stub (e.g., test_apify_client.py)           │
  │ 2. Implement the test (replace pass with real assertions)   │
  │ 3. Run test → It FAILS (module doesn't exist yet)          │
  └─────────────────────────────────────────────────────────────┘
           ↓
  ┌─────────────────────────────────────────────────────────────┐
  │ PHASE 2: GREEN (Make It Pass)                               │
  ├─────────────────────────────────────────────────────────────┤
  │ 4. Create the module (src/scrapers/apify_client.py)        │
  │ 5. Write minimal code to make test pass                     │
  │ 6. Run test → It PASSES ✓                                  │
  └─────────────────────────────────────────────────────────────┘
           ↓
  ┌─────────────────────────────────────────────────────────────┐
  │ PHASE 3: REFACTOR (Clean Up)                                │
  ├─────────────────────────────────────────────────────────────┤
  │ 7. Improve code quality while tests stay green             │
  │ 8. Add error handling, logging, documentation              │
  │ 9. Run tests again → Still PASSES ✓                        │
  └─────────────────────────────────────────────────────────────┘

  Practical Example: Building ApifyClient

  Let me show you exactly how you'd use the test stubs:

  Step 1: Pick First Test Stub
  # tests/unit/test_apify_client.py (line 17)
  def test_run_google_maps_scraper_success():
      """
      Given a valid Apify API key and search parameters
      When run_google_maps_scraper is called with search_query and max_results
      Then it should trigger the Apify actor and return a run_id
      """
      pass  # ← You'll replace this

  Step 2: Implement the Test (RED phase)
  def test_run_google_maps_scraper_success():
      # Import the class (doesn't exist yet - this will fail)
      from src.scrapers.apify_client import ApifyClient

      # Mock the Apify SDK
      with patch('apify_client.ApifyClient') as mock_apify:
          mock_actor = Mock()
          mock_actor.call.return_value = {"id": "run_123"}
          mock_apify.return_value.actor.return_value = mock_actor

          # Create our client
          client = ApifyClient(api_key="test_key")

          # Call the method we need to build
          result = client.run_google_maps_scraper(
              search_query="veterinary practices in CA",
              max_results=150
          )

          # Assert expectations
          assert result == "run_123"
          mock_actor.call.assert_called_once_with(
              actor_id="compass/crawler-google-places",
              run_input={
                  "searchQuery": "veterinary practices in CA",
                  "maxResults": 150
              }
          )

  Step 3: Run Test (It Will FAIL - RED)
  pytest tests/unit/test_apify_client.py::test_run_google_maps_scraper_success -v

  # Output:
  # ModuleNotFoundError: No module named 'src.scrapers.apify_client'
  # ❌ TEST FAILED (expected - this is RED phase)

  Step 4: Create Module (GREEN phase)
  # src/scrapers/apify_client.py (NEW FILE)
  from apify_client import ApifyClient as ApifySDK

  class ApifyClient:
      def __init__(self, api_key: str):
          self.client = ApifySDK(token=api_key)

      def run_google_maps_scraper(
          self, 
          search_query: str, 
          max_results: int
      ) -> str:
          """Run Google Maps scraper and return run_id"""
          actor = self.client.actor("compass/crawler-google-places")
          result = actor.call(
              run_input={
                  "searchQuery": search_query,
                  "maxResults": max_results
              }
          )
          return result["id"]

  Step 5: Run Test Again (It PASSES - GREEN)
  pytest tests/unit/test_apify_client.py::test_run_google_maps_scraper_success -v

  # Output:
  # test_run_google_maps_scraper_success PASSED ✓

  Step 6: Refactor & Add More Tests
  Now implement the next test stub, repeat the cycle.

  Test-to-Code Mapping

  Here's exactly which test file maps to which source code file:

  | Test File                                    | Creates Source File           | Purpose                |
  |----------------------------------------------|-------------------------------|------------------------|
  | tests/unit/test_apify_client.py              | src/scrapers/apify_client.py  | Apify actor wrapper    |
  | tests/unit/test_data_filter.py               | src/processing/data_filter.py | Hard filters           |
  | tests/unit/test_initial_scorer.py            | src/scoring/initial_scorer.py | Baseline scoring       |
  | tests/unit/test_notion_mapper.py             | src/mappers/notion_mapper.py  | Apify→Notion transform |
  | tests/unit/test_notion_batch.py              | src/uploaders/notion_batch.py | Batch upload logic     |
  | tests/integration/test_scraping_pipeline.py  | (tests component interaction) | Pipeline flow          |
  | tests/integration/test_notion_integration.py | (tests Notion API)            | Notion integration     |
  | tests/e2e/test_batch_operation.py            | src/main.py (CLI)             | Full pipeline          |

  Running Tests During Development

  Run single test while developing:
  # Test just one function
  pytest tests/unit/test_apify_client.py::test_run_google_maps_scraper_success -v

  # Test entire file
  pytest tests/unit/test_apify_client.py -v

  # Test with coverage
  pytest tests/unit/test_apify_client.py --cov=src.scrapers.apify_client --cov-report=html

  Run all tests for a component:
  pytest tests/unit/ -v  # All unit tests
  pytest tests/integration/ -v  # All integration tests
  pytest tests/e2e/ -v  # All E2E tests

  Run tests matching acceptance criteria:
  # Find all tests for AC-FEAT-001-001
  grep -r "AC-FEAT-001-001" tests/
  pytest -k "AC-FEAT-001-001"

  Recommended Development Order

  Based on the architecture, build in this order:

  1. Foundation (Unit Tests First)
  Day 1: ApifyClient
    → Implement test_apify_client.py tests one by one
    → Build src/scrapers/apify_client.py to make tests pass

  Day 2: DataFilter + InitialScorer  
    → Implement test_data_filter.py tests
    → Build src/processing/data_filter.py
    → Implement test_initial_scorer.py tests
    → Build src/scoring/initial_scorer.py

  Day 3: Notion Integration
    → Implement test_notion_mapper.py tests
    → Build src/mappers/notion_mapper.py
    → Implement test_notion_batch.py tests
    → Build src/uploaders/notion_batch.py

  2. Integration (Integration Tests)
  Day 4: Pipeline Integration
    → Implement test_scraping_pipeline.py tests
    → Connect components together
    → Implement test_notion_integration.py tests
    → Test full data flow

  3. End-to-End (E2E Tests)
  Day 5: CLI and Full Pipeline
    → Implement test_batch_operation.py tests
    → Build CLI entry point (main.py)
    → Test with --test flag (10 practices)

  Checking Progress

  See which tests are still stubs:
  # Count TODO stubs remaining
  grep -r "# TODO" tests/ | wc -l

  # List all unimplemented tests
  grep -r "pass$" tests/unit/test_apify_client.py

  Track acceptance criteria coverage:
  # See which AC criteria are tested
  grep -r "AC-FEAT-001" tests/ | cut -d: -f2 | sort | uniq

  Visual Progress Tracker

  Create this checklist as you work:

  ## FEAT-001 Implementation Progress

  ### Unit Tests (31 tests)
  - [ ] ApifyClient (7 tests)
    - [ ] test_run_google_maps_scraper_success
    - [ ] test_run_google_maps_scraper_retry_on_failure
    - [ ] test_wait_for_results_success
    - [ ] test_wait_for_results_timeout
    - [ ] test_parse_results_valid_data
    - [ ] test_parse_results_invalid_data
    - [ ] test_apify_client_missing_api_key

  - [ ] DataFilter (6 tests)
  - [ ] InitialScorer (5 tests)  
  - [ ] NotionMapper (5 tests)
  - [ ] NotionBatch (8 tests)

  ### Integration Tests (15 tests)
  - [ ] Scraping Pipeline (5 tests)
  - [ ] Notion Integration (6 tests)
  - [ ] Retry Logic (4 tests)

  ### E2E Tests (6 tests)
  - [ ] Full Pipeline Test Mode (6 tests)

  ### Acceptance Criteria Met: 0/30

  Key Advantages of This Approach

  1. Clear Requirements: Each test shows exactly what the code should do
  2. No Guesswork: Test stubs tell you what methods/functions to create
  3. Confidence: Green tests = working code
  4. Regression Protection: Tests catch bugs when you refactor
  5. Documentation: Tests show how to use your code
  6. Acceptance Criteria Traceability: Each test links to AC-FEAT-001-XXX

  What If Tests Are Unclear?

  Reference the planning docs:

  - acceptance.md: Clarifies WHAT needs to work (Given/When/Then)
  - architecture.md: Clarifies HOW components connect
  - testing.md: Clarifies test strategy and mock requirements

  Want me to walk through implementing one complete test together as an example? I can show you the full TDD cycle for one component like ApifyClient or
  DataFilter.