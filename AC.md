# Acceptance Criteria (Global)

**Purpose:** Central repository of all acceptance criteria across features

**Format:** AC-FEAT-XXX-### for feature-specific criteria, AC-GLOBAL-### for project-wide standards

---

## Global Standards

### AC-GLOBAL-001: Documentation Completeness
All features must have complete planning documentation before implementation (PRD, research, architecture, acceptance, testing, manual-test).

### AC-GLOBAL-002: Template Compliance
All planning documents must follow templates exactly with all required sections present.

### AC-GLOBAL-003: Word Limits
Planning documents must respect word limits: PRD ≤800 words, research ≤1000 words, others ≤800 words.

### AC-GLOBAL-004: Test Stubs Required
All features must have test stubs generated in tests/ directory with TODO comments and acceptance criteria references.

### AC-GLOBAL-005: Reviewer Validation
All planning workflows must pass Reviewer agent validation before being marked complete.

### AC-GLOBAL-006: No Placeholders
Planning documents must not contain TODO, TBD, or placeholder content (except in test stubs).

### AC-GLOBAL-007: Given/When/Then Format
All acceptance criteria must use Given/When/Then format for testability.

---

## Feature-Specific Criteria

*Feature acceptance criteria will be appended here by the Planner agent during `/plan` command*

### FEAT-001: Example Feature

**AC-FEAT-001-001:** Example Documentation Complete
Given a developer is using the AI workflow template, when they review FEAT-001 example feature, then all 6 planning documents are present and follow templates.

**AC-FEAT-001-002:** Templates Demonstrated
Given an AI agent is generating feature documentation, when the agent references FEAT-001 as an example, then the agent can replicate the structure and quality.

---

*New feature criteria will be appended here automatically during planning*

---

## FEAT-000: Shared Infrastructure

### AC-FEAT-000-001: Environment Variable Loading
**Given** a `.env` file with required configuration variables
**When** the application initializes
**Then** all configuration values are loaded correctly with proper type coercion
**And** missing required fields raise clear validation errors

### AC-FEAT-000-002: Nested Configuration Models
**Given** complex configuration with API keys and Notion settings
**When** configuration is loaded
**Then** nested models validate correctly (e.g., `notion.api_key`, `notion.database_id`)
**And** invalid nested values raise specific field errors

### AC-FEAT-000-003: Configuration Validation
**Given** invalid configuration values (wrong type, missing required fields)
**When** application attempts to load configuration
**Then** Pydantic validation errors are raised with clear field names
**And** error messages indicate expected type and constraints

### AC-FEAT-000-005: ANSI Console Logging
**Given** the application is running in an interactive terminal
**When** logs are emitted at different severity levels (DEBUG, INFO, WARNING, ERROR)
**Then** each level displays with appropriate ANSI color (blue, green, yellow, red)
**And** log format includes timestamp, level, and message

### AC-FEAT-000-006: File Logging Without ANSI
**Given** logs are written to a file
**When** log entries are created
**Then** ANSI color codes are stripped from file output
**And** logs remain readable in plain text editors

### AC-FEAT-000-007: Test Mode Debug Logging
**Given** the application is started with `--test` flag
**When** logging is initialized
**Then** log level automatically switches to DEBUG
**And** debug messages are visible in output

### AC-FEAT-000-008: Cost Tracking in Logs
**Given** an API call with known cost estimation
**When** the call is logged
**Then** log entry includes estimated cost in USD
**And** retry attempts log cumulative cost

### AC-FEAT-000-010: Exponential Backoff Retry
**Given** a transient API failure (HTTP 429, 503, or timeout)
**When** retry logic is triggered
**Then** requests are retried with exponential backoff (1s, 2s, 4s, 8s, 16s)
**And** maximum retry limit (5 attempts) is respected

### AC-FEAT-000-011: Cost Logging per Retry
**Given** a retryable API call that fails and retries
**When** each retry attempt occurs
**Then** estimated cost is logged for each attempt
**And** cumulative cost is trackable across retries

### AC-FEAT-000-013: Non-Retryable Error Handling
**Given** a non-retryable error (HTTP 400, 401, 403)
**When** the error occurs
**Then** no retry attempts are made
**And** error is raised immediately with clear categorization

### AC-FEAT-000-015: Notion Schema Validation
**Given** a Notion database connection
**When** the connection is initialized
**Then** expected properties are validated to exist
**And** missing critical properties raise clear errors

### AC-FEAT-000-016: Places API to Notion Mapping
**Given** a Google Places API response
**When** data is mapped to Notion format
**Then** all fields are transformed correctly (name, address, phone, hours, etc.)
**And** missing fields are handled gracefully with null/empty values

### AC-FEAT-000-017: Malformed Data Handling
**Given** malformed or unexpected data from Places API
**When** mapping to Notion format
**Then** errors are caught and logged with specific field context
**And** partial data is preserved where possible

### AC-FEAT-000-020: Place ID Caching
**Given** batch processing of multiple places
**When** the same Place ID is encountered multiple times
**Then** cached data is used instead of making redundant API calls
**And** cache is cleared at end of batch operation

### AC-FEAT-000-021: Cache Performance
**Given** a batch operation with 100 places, 20% duplicates
**When** Place ID caching is enabled
**Then** API calls are reduced by ~20%
**And** cache lookup overhead is less than 1ms per lookup

### AC-FEAT-000-022: Configuration Load Performance
**Given** application startup with valid configuration
**When** configuration is loaded and validated
**Then** total load time is less than 100ms
**And** no blocking I/O occurs during load

### AC-FEAT-000-023: Logging Performance Overhead
**Given** high-frequency logging (100+ log entries per second)
**When** logs are emitted
**Then** logging overhead is less than 5ms per entry
**And** application performance is not degraded

---

## FEAT-001: Google Maps Scraping & Notion Integration

### Functional Acceptance Criteria

**AC-FEAT-001-001: Successful Google Maps Scraping**
**Given** a valid Apify API key and search query "veterinary practices in California"
**When** the scraper runs with max_results=150
**Then** it should return 150 unique Google Maps results with Place ID, name, address, phone, website, reviews, and rating
**Priority:** Must Have

**AC-FEAT-001-002: Website Filter Applied**
**Given** scraped Google Maps results
**When** the data filter processes the results
**Then** it should exclude all practices without a website URL
**Priority:** Must Have

**AC-FEAT-001-003: Minimum Reviews Filter Applied**
**Given** scraped Google Maps results
**When** the data filter processes the results with min_reviews=10
**Then** it should exclude all practices with fewer than 10 reviews
**Priority:** Must Have

**AC-FEAT-001-004: Open Status Filter Applied**
**Given** scraped Google Maps results
**When** the data filter processes the results
**Then** it should exclude all practices marked as permanently closed
**Priority:** Must Have

**AC-FEAT-001-005: Initial Score Calculation**
**Given** a filtered practice with 50 reviews, 4.5 star rating, and website
**When** the initial scorer calculates the score
**Then** it should return a score between 0-25 points based on the scoring formula
**Priority:** Must Have

**AC-FEAT-001-006: Batch Upsert to Notion**
**Given** 30 scored practices ready for upload
**When** the Notion batch upserter processes them
**Then** it should create 30 new Notion pages in the target database in batches of 10 with 3.5s delays
**Priority:** Must Have

**AC-FEAT-001-007: Test Mode Execution**
**Given** the CLI is invoked with --test flag
**When** the pipeline runs
**Then** it should scrape exactly 10 practices and complete the full pipeline (filter, score, upload)
**Priority:** Must Have

**AC-FEAT-001-008: De-duplication by Place ID (Within Batch)**
**Given** scraping results contain 3 practices with the same Place ID
**When** the de-duplication logic runs
**Then** it should keep only 1 instance of each Place ID
**Priority:** Must Have

**AC-FEAT-001-009: De-duplication by Place ID (Cross-Batch)**
**Given** Notion database already contains a practice with Place ID "ChIJ123"
**When** the upserter attempts to upload a practice with Place ID "ChIJ123"
**Then** it should skip the duplicate and log a warning
**Priority:** Must Have

**AC-FEAT-001-010: Notion Schema Compliance**
**Given** a scored practice with all required fields
**When** the Notion mapper transforms it to Notion format
**Then** the payload should contain properties: Place ID (Title), Business Name (Rich Text), Address (Rich Text), Phone (Phone Number), Website (URL), Review Count (Number), Star Rating (Number), Initial Score (Number), Status (Select = "New Lead")
**Priority:** Must Have

### Edge Cases & Error Scenarios

**AC-FEAT-001-011: Empty Scraping Results**
**Given** a search query that returns 0 results
**When** the pipeline processes the empty list
**Then** it should log "No results found" and exit gracefully without errors
**Priority:** Must Have

**AC-FEAT-001-012: Apify API Failure with Retry**
**Given** Apify API returns a 500 error on the first 2 attempts
**When** the ApifyClient calls the API
**Then** it should retry up to 3 times with exponential backoff and succeed on the 3rd attempt
**Priority:** Must Have

**AC-FEAT-001-013: Apify API Timeout**
**Given** Apify actor run exceeds 600 seconds
**When** the ApifyClient waits for results
**Then** it should timeout and raise a TimeoutError with the run ID in the error message
**Priority:** Must Have

**AC-FEAT-001-014: Notion API Rate Limit (429)**
**Given** Notion API returns a 429 rate limit error
**When** the NotionBatchUpserter attempts to create a page
**Then** it should retry with exponential backoff (1s, 2s, 4s, 8s) up to 5 times
**Priority:** Must Have

**AC-FEAT-001-015: Notion API Server Error (5xx)**
**Given** Notion API returns a 500 server error
**When** the NotionBatchUpserter attempts to create a page
**Then** it should retry up to 5 times with exponential backoff
**Priority:** Must Have

**AC-FEAT-001-016: Invalid Practice Data**
**Given** a practice missing required fields (e.g., no Place ID)
**When** Pydantic validates the data model
**Then** it should raise a ValidationError and log the invalid record details
**Priority:** Must Have

**AC-FEAT-001-017: Partial Batch Failure**
**Given** a batch of 10 practices where 2 fail Notion validation
**When** the NotionBatchUpserter processes the batch
**Then** it should upload the 8 valid practices and log errors for the 2 failed practices
**Priority:** Should Have

**AC-FEAT-001-018: Missing Environment Variables**
**Given** APIFY_API_KEY environment variable is not set
**When** the pipeline initializes
**Then** it should raise a ConfigurationError with message "Missing required environment variable: APIFY_API_KEY"
**Priority:** Must Have

### Non-Functional Requirements

**AC-FEAT-001-019: Performance - Execution Time**
**Given** a production run with 150 practices
**When** the pipeline executes end-to-end
**Then** it should complete within 8 minutes (480 seconds)
**Priority:** Must Have

**AC-FEAT-001-020: Performance - Cost Efficiency**
**Given** a production run with 150 practices
**When** Apify charges are calculated
**Then** the total cost should be less than $2.00
**Priority:** Must Have

**AC-FEAT-001-021: Security - API Key Protection**
**Given** the application is running
**When** logs are written to stdout or files
**Then** API keys should never be logged in plaintext (should be masked)
**Priority:** Must Have

**AC-FEAT-001-022: Data Quality - Validation**
**Given** any practice data flowing through the pipeline
**When** Pydantic models validate the data
**Then** all required fields must be present and correctly typed
**Priority:** Must Have

**AC-FEAT-001-023: Observability - Structured Logging**
**Given** the pipeline is executing
**When** log messages are generated
**Then** they should be in JSON format with timestamp, level, message, and context fields
**Priority:** Should Have

### Integration Requirements

**AC-FEAT-001-024: Apify Actor Integration**
**Given** the ApifyClient is configured with a valid API key
**When** it calls the compass/crawler-google-places actor
**Then** it should use the correct actor ID and input schema (searchQuery, maxResults, filters)
**Priority:** Must Have

**AC-FEAT-001-025: Notion Database Schema**
**Given** the Notion database exists with ID 2a0edda2a9a081d98dc9daa43c65e744
**When** the pipeline queries or creates pages
**Then** the database must have properties: Place ID (Title), Business Name (Rich Text), Address (Rich Text), Phone (Phone Number), Website (URL), Review Count (Number), Star Rating (Number), Initial Score (Number), Status (Select)
**Priority:** Must Have

**AC-FEAT-001-026: Notion Batch Rate Limiting**
**Given** the NotionBatchUpserter is configured with batch_size=10
**When** it processes 30 practices
**Then** it should create exactly 3 API requests with 3.5 second delays between each batch
**Priority:** Must Have

### Data Requirements

**AC-FEAT-001-027: Place ID Uniqueness**
**Given** practices from any source
**When** they are de-duplicated
**Then** Place ID should be the unique identifier (no two practices with the same Place ID)
**Priority:** Must Have

**AC-FEAT-001-028: Score Range Validation**
**Given** any calculated initial score
**When** it is validated
**Then** it must be between 0 and 25 (inclusive)
**Priority:** Must Have

**AC-FEAT-001-029: Star Rating Validation**
**Given** any practice star rating
**When** it is validated
**Then** it must be between 0.0 and 5.0 (inclusive)
**Priority:** Must Have

**AC-FEAT-001-030: Website URL Format**
**Given** any practice website field
**When** it is validated
**Then** it must be a valid URL starting with http:// or https://
**Priority:** Must Have

---

**Note:** This file is append-only. Criteria are added by agents during `/plan` command and should not be manually edited or removed.

**Last Updated:** 2025-11-03
