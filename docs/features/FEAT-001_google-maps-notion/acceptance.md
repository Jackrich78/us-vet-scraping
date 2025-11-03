# Acceptance Criteria
**Feature:** FEAT-001 - Google Maps Scraping & Notion Integration
**Date:** 2025-11-03
**Version:** 1.0

## Overview

This document defines testable acceptance criteria for the Google Maps scraping and Notion integration feature. Each criterion follows the Given/When/Then format and is assigned a unique ID for traceability.

## User Stories

### Story 1: Scrape Veterinary Practices
As a sales team member, I want to automatically scrape veterinary practices from Google Maps so that I can build a lead pipeline without manual research.

### Story 2: Filter High-Quality Leads
As a sales team member, I want to filter practices by quality criteria (website, reviews, open status) so that I focus on qualified leads.

### Story 3: Score Leads Automatically
As a sales team member, I want practices scored automatically so that I can prioritize outreach to high-potential leads.

### Story 4: Push to Notion Database
As a sales team member, I want scraped leads pushed to Notion so that I can manage and track them in our CRM.

## Functional Acceptance Criteria

### AC-FEAT-001-001: Successful Google Maps Scraping
**Given** a valid Apify API key and search query "veterinary practices in California"
**When** the scraper runs with max_results=150
**Then** it should return 150 unique Google Maps results with Place ID, name, address, phone, website, reviews, and rating
**Priority:** Must Have

### AC-FEAT-001-002: Website Filter Applied
**Given** scraped Google Maps results
**When** the data filter processes the results
**Then** it should exclude all practices without a website URL
**Priority:** Must Have

### AC-FEAT-001-003: Minimum Reviews Filter Applied
**Given** scraped Google Maps results
**When** the data filter processes the results with min_reviews=10
**Then** it should exclude all practices with fewer than 10 reviews
**Priority:** Must Have

### AC-FEAT-001-004: Open Status Filter Applied
**Given** scraped Google Maps results
**When** the data filter processes the results
**Then** it should exclude all practices marked as permanently closed
**Priority:** Must Have

### AC-FEAT-001-005: Initial Score Calculation
**Given** a filtered practice with 50 reviews, 4.5 star rating, and website
**When** the initial scorer calculates the score
**Then** it should return a score between 0-25 points based on the scoring formula
**Priority:** Must Have

### AC-FEAT-001-006: Batch Upsert to Notion
**Given** 30 scored practices ready for upload
**When** the Notion batch upserter processes them
**Then** it should create 30 new Notion pages in the target database in batches of 10 with 3.5s delays
**Priority:** Must Have

### AC-FEAT-001-007: Test Mode Execution
**Given** the CLI is invoked with --test flag
**When** the pipeline runs
**Then** it should scrape exactly 10 practices and complete the full pipeline (filter, score, upload)
**Priority:** Must Have

### AC-FEAT-001-008: De-duplication by Place ID (Within Batch)
**Given** scraping results contain 3 practices with the same Place ID
**When** the de-duplication logic runs
**Then** it should keep only 1 instance of each Place ID
**Priority:** Must Have

### AC-FEAT-001-009: De-duplication by Place ID (Cross-Batch)
**Given** Notion database already contains a practice with Place ID "ChIJ123"
**When** the upserter attempts to upload a practice with Place ID "ChIJ123"
**Then** it should skip the duplicate and log a warning
**Priority:** Must Have

### AC-FEAT-001-010: Notion Schema Compliance
**Given** a scored practice with all required fields
**When** the Notion mapper transforms it to Notion format
**Then** the payload should contain properties: Place ID (Title), Business Name (Rich Text), Address (Rich Text), Phone (Phone Number), Website (URL), Review Count (Number), Star Rating (Number), Initial Score (Number), Status (Select = "New Lead")
**Priority:** Must Have

## Edge Cases & Error Scenarios

### AC-FEAT-001-011: Empty Scraping Results
**Given** a search query that returns 0 results
**When** the pipeline processes the empty list
**Then** it should log "No results found" and exit gracefully without errors
**Priority:** Must Have

### AC-FEAT-001-012: Apify API Failure with Retry
**Given** Apify API returns a 500 error on the first 2 attempts
**When** the ApifyClient calls the API
**Then** it should retry up to 3 times with exponential backoff and succeed on the 3rd attempt
**Priority:** Must Have

### AC-FEAT-001-013: Apify API Timeout
**Given** Apify actor run exceeds 600 seconds
**When** the ApifyClient waits for results
**Then** it should timeout and raise a TimeoutError with the run ID in the error message
**Priority:** Must Have

### AC-FEAT-001-014: Notion API Rate Limit (429)
**Given** Notion API returns a 429 rate limit error
**When** the NotionBatchUpserter attempts to create a page
**Then** it should retry with exponential backoff (1s, 2s, 4s, 8s) up to 5 times
**Priority:** Must Have

### AC-FEAT-001-015: Notion API Server Error (5xx)
**Given** Notion API returns a 500 server error
**When** the NotionBatchUpserter attempts to create a page
**Then** it should retry up to 5 times with exponential backoff
**Priority:** Must Have

### AC-FEAT-001-016: Invalid Practice Data
**Given** a practice missing required fields (e.g., no Place ID)
**When** Pydantic validates the data model
**Then** it should raise a ValidationError and log the invalid record details
**Priority:** Must Have

### AC-FEAT-001-017: Partial Batch Failure
**Given** a batch of 10 practices where 2 fail Notion validation
**When** the NotionBatchUpserter processes the batch
**Then** it should upload the 8 valid practices and log errors for the 2 failed practices
**Priority:** Should Have

### AC-FEAT-001-018: Missing Environment Variables
**Given** APIFY_API_KEY environment variable is not set
**When** the pipeline initializes
**Then** it should raise a ConfigurationError with message "Missing required environment variable: APIFY_API_KEY"
**Priority:** Must Have

## Non-Functional Requirements

### AC-FEAT-001-019: Performance - Execution Time
**Given** a production run with 150 practices
**When** the pipeline executes end-to-end
**Then** it should complete within 8 minutes (480 seconds)
**Priority:** Must Have

### AC-FEAT-001-020: Performance - Cost Efficiency
**Given** a production run with 150 practices
**When** Apify charges are calculated
**Then** the total cost should be less than $2.00
**Priority:** Must Have

### AC-FEAT-001-021: Security - API Key Protection
**Given** the application is running
**When** logs are written to stdout or files
**Then** API keys should never be logged in plaintext (should be masked)
**Priority:** Must Have

### AC-FEAT-001-022: Data Quality - Validation
**Given** any practice data flowing through the pipeline
**When** Pydantic models validate the data
**Then** all required fields must be present and correctly typed
**Priority:** Must Have

### AC-FEAT-001-023: Observability - Structured Logging
**Given** the pipeline is executing
**When** log messages are generated
**Then** they should be in JSON format with timestamp, level, message, and context fields
**Priority:** Should Have

## Integration Requirements

### AC-FEAT-001-024: Apify Actor Integration
**Given** the ApifyClient is configured with a valid API key
**When** it calls the compass/crawler-google-places actor
**Then** it should use the correct actor ID and input schema (searchQuery, maxResults, filters)
**Priority:** Must Have

### AC-FEAT-001-025: Notion Database Schema
**Given** the Notion database exists with ID 2a0edda2a9a081d98dc9daa43c65e744
**When** the pipeline queries or creates pages
**Then** the database must have properties: Place ID (Title), Business Name (Rich Text), Address (Rich Text), Phone (Phone Number), Website (URL), Review Count (Number), Star Rating (Number), Initial Score (Number), Status (Select)
**Priority:** Must Have

### AC-FEAT-001-026: Notion Batch Rate Limiting
**Given** the NotionBatchUpserter is configured with batch_size=10
**When** it processes 30 practices
**Then** it should create exactly 3 API requests with 3.5 second delays between each batch
**Priority:** Must Have

## Data Requirements

### AC-FEAT-001-027: Place ID Uniqueness
**Given** practices from any source
**When** they are de-duplicated
**Then** Place ID should be the unique identifier (no two practices with the same Place ID)
**Priority:** Must Have

### AC-FEAT-001-028: Score Range Validation
**Given** any calculated initial score
**When** it is validated
**Then** it must be between 0 and 25 (inclusive)
**Priority:** Must Have

### AC-FEAT-001-029: Star Rating Validation
**Given** any practice star rating
**When** it is validated
**Then** it must be between 0.0 and 5.0 (inclusive)
**Priority:** Must Have

### AC-FEAT-001-030: Website URL Format
**Given** any practice website field
**When** it is validated
**Then** it must be a valid URL starting with http:// or https://
**Priority:** Must Have

## Completion Checklist

- [ ] All 30 acceptance criteria implemented
- [ ] Test stubs created for each criterion
- [ ] Unit tests cover ApifyClient, DataFilter, InitialScorer, NotionMapper, NotionBatchUpserter
- [ ] Integration tests cover full pipeline with mocked APIs
- [ ] E2E test validates test mode (--test flag with 10 practices)
- [ ] Manual testing completed per manual-test.md
- [ ] All tests pass with >80% code coverage
- [ ] Performance benchmarks met (<8 min, <$2)
- [ ] Security review passed (no API keys in logs)
- [ ] Documentation updated (README, deployment guide)

---

**Total Criteria:** 30
**Must Have:** 27
**Should Have:** 3
**Template Version:** 1.0.0
**Last Updated:** 2025-11-03
