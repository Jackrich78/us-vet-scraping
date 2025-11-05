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

## FEAT-002: Website Enrichment & LLM Extraction

### Functional Acceptance Criteria

**AC-FEAT-002-001: Multi-Page Website Scraping**
**Given** a veterinary practice with website URL "https://example-vet.com"
**When** WebsiteScraper scrapes with BFSDeepCrawlStrategy (max_depth=1, max_pages=5)
**Then** it should return 2-4 pages successfully scraped (homepage + /about + /team pages)

**AC-FEAT-002-002: Concurrent Practice Scraping**
**Given** 150 practices needing enrichment
**When** EnrichmentOrchestrator processes them with max_concurrent=5
**Then** it should scrape 5 practices concurrently, completing all 150 within 10-12 minutes

**AC-FEAT-002-003: OpenAI Structured Output Extraction**
**Given** scraped website pages with cleaned text (homepage + /about + /team)
**When** LLMExtractor extracts data using beta.chat.completions.parse with VetPracticeExtraction model
**Then** it should return 100% valid Pydantic object with all fields populated or null

**AC-FEAT-002-004: Vet Count Extraction with Confidence**
**Given** website text mentions "Dr. Jane Smith, Dr. John Doe, Dr. Mary Johnson"
**When** LLMExtractor analyzes the text
**Then** it should extract vet_count_total=3 with vet_count_confidence="high"

**AC-FEAT-002-005: Decision Maker Extraction (Explicit Email Only)**
**Given** website shows "Contact Dr. Smith (Owner) at drsmith@example.com"
**When** LLMExtractor analyzes the text
**Then** it should extract decision_maker.name="Dr. Smith", decision_maker.role="Owner", decision_maker.email="drsmith@example.com"

**AC-FEAT-002-006: Service Detection (24/7 Emergency)**
**Given** website text states "We offer 24/7 emergency services"
**When** LLMExtractor analyzes the text
**Then** it should set emergency_24_7=True

**AC-FEAT-002-007: Technology Indicator Detection**
**Given** website has "Book appointments online" and "Patient portal login"
**When** LLMExtractor analyzes the text
**Then** it should set online_booking=True and patient_portal=True

**AC-FEAT-002-008: Personalization Context Extraction**
**Given** website mentions "Opened 2nd location in Newton Oct 2024" and "AAHA accredited"
**When** LLMExtractor analyzes the text
**Then** it should populate personalization_context=["Opened 2nd location in Newton Oct 2024"] and awards_accreditations=["AAHA accredited"]

**AC-FEAT-002-009: Cost Tracking with tiktoken**
**Given** LLMExtractor is about to call OpenAI API with 2000 input tokens + 500 estimated output tokens
**When** CostTracker.check_budget() is called
**Then** it should calculate estimated_cost = (2000 × $0.15/1M) + (500 × $0.60/1M) = $0.0006

**AC-FEAT-002-010: Cost Abort Threshold**
**Given** cumulative OpenAI cost has reached $0.95
**When** CostTracker.check_budget(estimated_cost=$0.08) is called
**Then** it should raise CostLimitExceeded with message "Cost limit exceeded: $0.95 + $0.08 > $1.00"

**AC-FEAT-002-011: Notion Partial Update (Field Preservation)**
**Given** existing Notion record with Status="Qualified", Assigned To="John", Call Notes="Follow up next week"
**When** NotionClient.update_practice_enrichment() updates only enrichment fields
**Then** Status, Assigned To, and Call Notes should remain unchanged

**AC-FEAT-002-012: Enrichment Status Update**
**Given** successful enrichment with all data extracted
**When** NotionClient updates the practice record
**Then** it should set enrichment_status="Completed" and last_enrichment_date=current_timestamp

**AC-FEAT-002-013: Re-enrichment Filter (30-Day Threshold)**
**Given** Notion database with 200 practices, 50 enriched <30 days ago, 100 enriched >30 days ago, 50 never enriched
**When** EnrichmentOrchestrator queries Notion for practices needing enrichment
**Then** it should return 150 practices (100 stale + 50 never enriched)

**AC-FEAT-002-014: Test Mode Execution (10 Practices)**
**Given** EnrichmentOrchestrator invoked with test_mode=True
**When** the pipeline runs
**Then** it should enrich exactly 10 practices (first 10 from Notion query) and complete within 1-2 minutes

**AC-FEAT-002-015: Automatic FEAT-003 Scoring Trigger**
**Given** auto_trigger_scoring=True and scoring_service is provided
**When** a practice is successfully enriched
**Then** ScoringService.calculate_icp_score() should be called with practice_id and enrichment_data

**AC-FEAT-002-016: Scoring Trigger Graceful Degradation**
**Given** auto_trigger_scoring=False OR scoring_service=None
**When** enrichment completes
**Then** pipeline should complete successfully without triggering scoring (no errors)

### Edge Cases & Error Handling

**AC-FEAT-002-101: Website Timeout (Individual Page)**
**Given** WebsiteScraper is crawling a practice website
**When** the /team page exceeds 30s timeout
**Then** it should mark /team page as failed (success=False) but continue with other pages (homepage, /about)

**AC-FEAT-002-102: Entire Practice Scraping Failure**
**Given** WebsiteScraper attempts to scrape a practice with broken website
**When** all pages fail to load
**Then** it should add practice to failed_practices list for retry at end of batch

**AC-FEAT-002-103: LLM Extraction Failure (Rate Limit)**
**Given** LLMExtractor calls OpenAI API during peak usage
**When** API returns 429 error
**Then** it should retry with exponential backoff (1s, 2s, 4s) up to 2 attempts total

**AC-FEAT-002-104: Low Confidence Extraction**
**Given** website text has vague mention "Our team of veterinarians"
**When** LLMExtractor analyzes the text
**Then** it should set vet_count_total=null, vet_count_confidence="low", and flag in Notion

**AC-FEAT-002-105: Empty Personalization Context**
**Given** website has only basic contact information (no awards, history, specialties)
**When** LLMExtractor analyzes the text
**Then** it should return personalization_context=[] (empty array)

**AC-FEAT-002-106: Failed Scrape Retry (End of Batch)**
**Given** 8 practices in failed_practices list at end of initial batch
**When** EnrichmentOrchestrator executes retry logic
**Then** it should re-attempt scraping for all 8 practices once

**AC-FEAT-002-107: Persistent Failure Logging to Notion**
**Given** a practice fails scraping twice
**When** retry completes with failure
**Then** NotionClient should update practice with enrichment_status="Failed" and enrichment_error="DNS resolution failed"

**AC-FEAT-002-108: Scoring Failure (FEAT-003 Error)**
**Given** auto_trigger_scoring=True and practice is successfully enriched
**When** ScoringService.calculate_icp_score() raises ScoringError
**Then** it should log error and continue with next practice (don't fail entire pipeline)

**AC-FEAT-002-109: No Decision Maker Email Found**
**Given** website lists "Dr. Jane Smith (Owner)" but no email contact
**When** LLMExtractor analyzes the text
**Then** it should set decision_maker.name="Dr. Jane Smith", decision_maker.role="Owner", decision_maker.email=null

**AC-FEAT-002-110: Cost Limit Exceeded Mid-Batch**
**Given** cumulative cost reaches $1.01 after 120 extractions
**When** CostTracker.check_budget() is called for practice #121
**Then** it should raise CostLimitExceeded and abort pipeline immediately

### Non-Functional Requirements

**AC-FEAT-002-201: Performance - Total Execution Time**
Total execution time ≤14 minutes for 150 practices (test mode: 10 practices within 1-2 minutes). Scraping ≤12 min, LLM ≤2 min, Notion ≤1 min, retry ≤2 min.

**AC-FEAT-002-202: Performance - Cost Efficiency**
Total OpenAI cost ≤$0.50 for 150 practices (per-extraction $0.0006 avg, base $0.09 + retries + buffer).

**AC-FEAT-002-203: Data Quality - Vet Count Detection**
Detect vet count for ≥60% of practices (multi-page improves from ~40% homepage-only). ≥90% of detected counts have confidence="high" or "medium".

**AC-FEAT-002-204: Data Quality - Decision Maker Email**
Find explicitly stated decision maker email for ≥50% of practices. 100% of found emails are explicitly stated on website (no pattern guessing).

**AC-FEAT-002-205: Data Quality - Personalization Context**
Find 1-3 personalization facts for ≥70% of practices. ≥40% have specific facts, ≥30% have generic facts.

**AC-FEAT-002-206: Reliability - Scraping Success Rate**
≥95% scraping success rate after retry (≤8 total failures out of 150). Initial success ≥90%, retry recovers ~50% of failures.

**AC-FEAT-002-207: Reliability - LLM Extraction Success Rate**
≥97% extraction success rate (≤5 failures out of 150). Retryable errors (429, timeout) handled with retry logic.

**AC-FEAT-002-208: Security - API Key Protection**
OpenAI API key never logged in plaintext. Masked in log outputs (e.g., "sk-proj-***"), not in error messages, loaded from environment variable.

**AC-FEAT-002-209: Observability - Cost Logging**
Log cumulative OpenAI cost every 10 practices. Format: "Cost update: $0.0060 / $1.00" (cumulative / threshold). Final report with total cost, practices enriched, cost per practice.

### Integration Requirements

**AC-FEAT-002-301: Crawl4AI BFSDeepCrawlStrategy Integration**
**Given** WebsiteScraper is initialized with BFSDeepCrawlStrategy
**When** it scrapes a practice website
**Then** it should use max_depth=1, max_pages=5, include_external=False, and URL pattern filter

**AC-FEAT-002-302: OpenAI Structured Outputs Integration**
**Given** LLMExtractor calls OpenAI API
**When** it uses beta.chat.completions.parse with VetPracticeExtraction model
**Then** response should be valid Pydantic object (no parsing errors)

**AC-FEAT-002-303: tiktoken Integration for Cost Tracking**
**Given** LLMExtractor is about to call OpenAI API
**When** it counts tokens with tiktoken.encoding_for_model("gpt-4o-mini")
**Then** token count should match actual API usage within 5%

**AC-FEAT-002-304: Notion API Partial Update Integration**
**Given** NotionClient.update_practice_enrichment() is called
**When** it sends update payload to Notion API
**Then** payload should contain only enrichment fields, not sales fields

**AC-FEAT-002-305: FEAT-003 Scoring Service Integration**
**Given** auto_trigger_scoring=True and scoring_service provided
**When** EnrichmentOrchestrator completes enrichment for a practice
**Then** it should call scoring_service.calculate_icp_score(practice_id, enrichment_data)

### Data Requirements

**AC-FEAT-002-401: Extraction Schema Validation**
All extracted data must conform to VetPracticeExtraction Pydantic model. Required fields, type safety, constraints (vet_count 1-50, confidence in ["high", "medium", "low"]), defaults set correctly.

**AC-FEAT-002-402: Notion Field Mapping**
Correctly map VetPracticeExtraction fields to Notion database properties. Type compatibility (number, rich_text, email), null handling (empty fields).

**AC-FEAT-002-403: Re-enrichment Date Tracking**
Track last_enrichment_date (Notion date property) set to extraction_timestamp. ISO 8601 datetime string format.

---

**Note:** This file is append-only. Criteria are added by agents during `/plan` command and should not be manually edited or removed.

# Acceptance Criteria: FEAT-003 ICP Lead Scoring

## Data Quality Scenarios
- **AC-FEAT-003-001:** Full Enrichment Data Scoring - Given a practice has complete enrichment data (vet count, services, reviews, decision maker, etc.), when the scoring algorithm runs, then all scoring components are calculated and summed to produce a score between 0-120 points
- **AC-FEAT-003-002:** Partial Enrichment Data Scoring - Given a practice has enrichment data with some missing fields, when the scoring algorithm runs, then missing fields contribute 0 points and the practice receives a reduced score based only on available data
- **AC-FEAT-003-003:** Low Confidence Enrichment Penalty - Given a practice has enrichment data marked with low confidence (< 0.8), when the scoring algorithm runs, then the final score is multiplied by 0.7 and confidence flags are set
- **AC-FEAT-003-004:** Baseline-Only Scoring (No Enrichment) - Given a practice has only Google Maps data, when the scoring algorithm runs, then only baseline components are scored with a maximum of 40 points
- **AC-FEAT-003-005:** Null Enrichment Data Handling - Given a practice has enrichment_data = None, when the scoring algorithm runs, then the system handles this gracefully and applies baseline-only scoring

## Scoring Algorithm Correctness
- **AC-FEAT-003-006:** Practice Size Sweet Spot - Given a practice has 3-8 confirmed veterinarians, when practice size is calculated, then the practice receives 25 points
- **AC-FEAT-003-007:** Practice Size Near Sweet Spot - Given a practice has exactly 2 or 9 veterinarians, when practice size is calculated, then the practice receives 15 points
- **AC-FEAT-003-008:** Practice Size Outside Sweet Spot - Given a practice has 1 or 10+ veterinarians, when practice size is calculated, then the practice receives 5 points
- **AC-FEAT-003-009:** Emergency 24/7 Services Bonus - Given a practice offers emergency services or 24/7 availability, when call volume is calculated, then the practice receives an additional 15 points
- **AC-FEAT-003-010:** Google Reviews Volume Scoring - Given a practice has Google reviews, when baseline is calculated, then the practice receives 20/12/5/0 points based on volume (100+/50-99/20-49/<20)
- **AC-FEAT-003-011:** Multiple Locations Bonus - Given a practice has multiple locations (location_count > 1), when call volume is calculated, then the practice receives an additional 10 points
- **AC-FEAT-003-012:** High-Value Services Bonus - Given a practice offers boarding or specialty services, when call volume is calculated, then the practice receives an additional 10 points
- **AC-FEAT-003-013:** Technology Adoption Scoring - Given a practice has technology features, when technology component is calculated, then the practice receives 10 points for online booking or 5 points for portal/telemedicine
- **AC-FEAT-003-014:** Google Rating Scoring - Given a practice has a Google rating, when baseline is calculated, then the practice receives 6/4/2/0 points based on rating (4.5+/4.0-4.4/3.5-3.9/<3.5)
- **AC-FEAT-003-015:** Website Presence Bonus - Given a practice has a website URL, when baseline is calculated, then the practice receives an additional 4 points
- **AC-FEAT-003-016:** Decision Maker Contact Scoring - Given enrichment includes decision maker info, when decision maker component is calculated, then the practice receives 10 points for name+email, 5 points for name only, or 0 points

## Confidence Penalty Application
- **AC-FEAT-003-017:** High Confidence No Penalty - Given enrichment confidence >= 0.9, when final score is calculated, then no confidence penalty is applied (score × 1.0)
- **AC-FEAT-003-018:** Medium Confidence Penalty - Given enrichment confidence 0.8-0.89, when final score is calculated, then the score is multiplied by 0.9
- **AC-FEAT-003-019:** Low Confidence Penalty - Given enrichment confidence < 0.8, when final score is calculated, then the score is multiplied by 0.7
- **AC-FEAT-003-020:** Low Confidence Vet Count Flag - Given enrichment has low confidence vet count, when scoring completes, then Confidence Flags includes "⚠️ Low Confidence Vet Count"

## Priority Tier Classification
- **AC-FEAT-003-021:** Hot Lead Classification - Given a practice has lead score 80-120, when priority tier is assigned, then the practice is classified as "🔥 Hot"
- **AC-FEAT-003-022:** Warm Lead Classification - Given a practice has lead score 50-79, when priority tier is assigned, then the practice is classified as "🌡️ Warm"
- **AC-FEAT-003-023:** Cold Lead Classification - Given a practice has lead score 0-49, when priority tier is assigned, then the practice is classified as "❄️ Cold"
- **AC-FEAT-003-024:** Solo Practice Out of Scope - Given a practice has 1 vet and score < 20, when priority tier is assigned, then the practice is classified as "⛔ Out of Scope"
- **AC-FEAT-003-025:** Corporate Practice Out of Scope - Given a practice has 10+ vets and score < 20, when priority tier is assigned, then the practice is classified as "⛔ Out of Scope"
- **AC-FEAT-003-026:** Pending Enrichment Classification - Given a practice has not been enriched yet, when priority tier is assigned, then the practice is classified as "⏳ Pending Enrichment"

## Score Breakdown JSON Structure
- **AC-FEAT-003-027:** Valid JSON Score Breakdown - Given scoring completes successfully, when Score Breakdown is written to Notion, then the content is valid JSON
- **AC-FEAT-003-028:** Complete Component Scores - Given scoring completes successfully, when Score Breakdown JSON is examined, then it includes all components: practice_size, call_volume, technology, baseline, decision_maker
- **AC-FEAT-003-029:** Confidence Penalty Details - Given a confidence penalty was applied, when Score Breakdown JSON is examined, then it includes penalty details with original score, multiplier, and final score
- **AC-FEAT-003-030:** Missing Field Notes - Given some enrichment fields are missing, when Score Breakdown JSON is examined, then it includes notes for missing fields

## Error Handling
- **AC-FEAT-003-031:** Scoring Error Logging - Given an error occurs during scoring, when the error is caught, then error details are logged to Score Breakdown as JSON
- **AC-FEAT-003-032:** Null Lead Score on Failure - Given scoring fails with unrecoverable error, when Notion is updated, then Lead Score is set to null
- **AC-FEAT-003-033:** Failed Scoring Status - Given scoring fails with error, when Notion is updated, then Scoring Status is set to "Failed"
- **AC-FEAT-003-034:** Enrichment Status Preservation - Given scoring fails after successful enrichment, when Notion is updated, then Enrichment Status remains "Completed"
- **AC-FEAT-003-035:** Scoring Timeout Enforcement - Given scoring takes longer than 5 seconds, when timeout is reached, then asyncio.TimeoutError is raised and status becomes "Failed"
- **AC-FEAT-003-036:** Auto-Trigger Failure Isolation - Given auto-triggered scoring fails, when error is handled, then failure is logged but does not propagate to FEAT-002
- **AC-FEAT-003-037:** Circuit Breaker Opens - Given 5 consecutive scoring failures occur, when threshold is reached, then circuit breaker opens and rejects subsequent requests
- **AC-FEAT-003-038:** Circuit Breaker Reset - Given circuit breaker is open, when 60 seconds elapse with no requests, then circuit breaker resets to closed state

## Dual Scoring System
- **AC-FEAT-003-039:** Initial Score Preservation - Given a practice has existing initial_score, when FEAT-003 scoring runs, then initial_score is never overwritten
- **AC-FEAT-003-040:** Independent Lead Score - Given a practice is scored by FEAT-003, when lead_score is calculated, then it is computed independently of initial_score
- **AC-FEAT-003-041:** Both Scores Visible - Given a practice has both initial_score and lead_score, when viewed in Notion, then both fields are visible
- **AC-FEAT-003-042:** Priority Tier from Lead Score - Given a practice has both scores, when priority tier is determined, then tier is based on lead_score (not initial_score)

## Integration with FEAT-002
- **AC-FEAT-003-043:** Auto-Trigger Enabled - Given auto_trigger_scoring=true in FEAT-002 config, when enrichment completes, then FEAT-003 scoring is automatically triggered
- **AC-FEAT-003-044:** Auto-Trigger Disabled - Given auto_trigger_scoring=false in FEAT-002 config, when enrichment completes, then FEAT-003 scoring is NOT triggered
- **AC-FEAT-003-045:** Receives Enrichment Data - Given FEAT-002 completes enrichment, when FEAT-003 is triggered, then scoring receives complete enrichment_data dictionary
- **AC-FEAT-003-046:** Handles Null Enrichment Data - Given FEAT-002 passes enrichment_data=None, when scoring processes practice, then baseline-only scoring is applied without errors

## Manual Rescore Command
- **AC-FEAT-003-047:** Rescore All Practices - Given command `--rescore all` is executed, when scoring system runs, then all practices are rescored regardless of status
- **AC-FEAT-003-048:** Rescore Single Practice - Given command `--rescore <practice-id>` is executed, when scoring runs, then only specified practice is rescored
- **AC-FEAT-003-049:** Rescore Unenriched Practice - Given manual rescore for practice without enrichment, when scoring runs, then baseline-only scoring is applied successfully
- **AC-FEAT-003-050:** Rescore Enriched Practice - Given manual rescore for practice with complete enrichment, when scoring runs, then full scoring algorithm is applied successfully
- **AC-FEAT-003-051:** Rescore Not Found Handling - Given manual rescore for non-existent practice ID, when system attempts to load practice, then error is logged and process exits cleanly

## Performance Requirements
- **AC-FEAT-003-052:** Single Practice Typical Performance - Given a practice with high-confidence enrichment, when scoring is executed, then scoring completes in less than 100ms
- **AC-FEAT-003-053:** Single Practice Timeout Enforcement - Given scoring is executed for any practice, when execution time is measured, then scoring never exceeds 5000ms
- **AC-FEAT-003-054:** Batch Scoring Performance - Given 150 practices need scoring, when batch scoring is executed, then all practices are scored in less than 15 seconds
- **AC-FEAT-003-055:** Baseline-Only Performance - Given a practice with only Google Maps data, when baseline-only scoring is executed, then scoring completes in less than 10ms

## State Management
- **AC-FEAT-003-056:** Scoring Status Update Success - Given scoring completes successfully, when Notion is updated, then Scoring Status changes from "Not Scored" to "Scored"
- **AC-FEAT-003-057:** Scoring Status Update Failure - Given scoring fails, when Notion is updated, then Scoring Status is set to "Failed"
- **AC-FEAT-003-058:** Confidence Flags Set - Given low-confidence data is detected, when Notion is updated, then appropriate confidence flags are added to Confidence Flags field
- **AC-FEAT-003-059:** Idempotent Scoring - Given same practice with identical enrichment is scored twice, when both runs complete, then both produce exact same lead_score

## Notion Field Updates
- **AC-FEAT-003-060:** Lead Score Field Update - Given scoring completes successfully, when Notion is updated, then Lead Score field (number, 0-120, nullable) contains calculated score
- **AC-FEAT-003-061:** Priority Tier Field Update - Given scoring completes successfully, when Notion is updated, then Priority Tier field (select, nullable) contains appropriate tier
- **AC-FEAT-003-062:** Score Breakdown Field Update - Given scoring completes successfully, when Notion is updated, then Score Breakdown field (rich_text) contains valid JSON with all components
- **AC-FEAT-003-063:** Confidence Flags Field Update - Given low-confidence data is detected, when Notion is updated, then Confidence Flags field (multi_select) contains warning flags
- **AC-FEAT-003-064:** Scoring Status Field Update - Given scoring completes (success or failure), when Notion is updated, then Scoring Status field reflects current state
- **AC-FEAT-003-065:** Sales Workflow Field Preservation - Given a practice has existing sales workflow data, when scoring updates Notion, then all sales workflow fields remain unchanged
- **AC-FEAT-003-066:** Enrichment Field Preservation - Given a practice has enrichment data, when scoring updates Notion, then all enrichment fields remain unchanged

## Configuration Management
- **AC-FEAT-003-067:** Load ScoringConfig - Given config.json contains scoring section, when scoring system initializes, then ScoringConfig is loaded successfully
- **AC-FEAT-003-068:** Validate Sweet Spot Range - Given ScoringConfig is loaded, when validation runs, then sweet_spot_min <= sweet_spot_max (raises error if invalid)
- **AC-FEAT-003-069:** Validate Timeout Positive - Given ScoringConfig is loaded, when validation runs, then timeout > 0 (raises error if zero or negative)
- **AC-FEAT-003-070:** Validate Confidence Multipliers - Given ScoringConfig is loaded, when validation runs, then all confidence multipliers are between 0.0 and 1.0 inclusive


**Last Updated:** 2025-11-05
